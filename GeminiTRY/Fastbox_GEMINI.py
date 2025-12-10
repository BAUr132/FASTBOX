import logging
import sqlite3
import json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    WebAppInfo,
    MenuButtonWebApp
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ==============================================================================
# НАСТРОЙКИ И КАТАЛОГИ
# ==============================================================================

API_TOKEN = ""  # Вставьте токен

# ID Администратора (видит все заказы)
ADMIN_IDS = [123456789]

# ID Курьеров (Вставьте сюда свой ID, чтобы сразу получить права курьера)
# Пример: APPROVED_COURIERS = [123456789, 987654321]
APPROVED_COURIERS = []

DB_FILE = "fastbox.db"
WEB_APP_URL = "https://baur132.github.io/FASTBOX/index.html"

# Каталоги товаров
CATALOGS = {
    "pharmacy": {
        "name": "🏥 Аптека",
        "items": {
            "💊 Обезбол (Нурофен)": 2500,
            "🍋 Витамин C": 1500,
            "🦠 Противовирусное": 3500,
            "🩹 Пластырь": 500,
            "🌡 Градусник": 2000
        }
    },
    "grocery": {
        "name": "🛒 Продукты",
        "items": {
            "🍞 Хлеб": 200,
            "🥛 Молоко 1л": 650,
            "🍚 Рис 1кг": 800,
            "💧 Вода 5л": 450,
            "🍫 Шоколад": 500,
            "🍎 Яблоки 1кг": 700
        }
    },
    "tech": {
        "name": "📱 Электроника",
        "items": {
            "🔌 Кабель USB-C": 3000,
            "🔋 Батарейки AA (4шт)": 1500,
            "🎧 Наушники простые": 4500,
            "🖱 Мышка": 3500
        }
    }
}

# ==============================================================================
# ЛОГИРОВАНИЕ И БД
# ==============================================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 user_id INTEGER PRIMARY KEY,
                 username TEXT,
                 full_name TEXT,
                 role TEXT DEFAULT 'guest',
                 phone TEXT,
                 last_address TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 client_id INTEGER,
                 courier_id INTEGER,
                 shop_type TEXT,
                 items TEXT,
                 addr_to TEXT,
                 goods_price INTEGER,
                 delivery_price INTEGER,
                 total_price INTEGER,
                 status TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')
    conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# --- Users ---
def db_upsert_user(user_id, username, full_name, role=None):
    conn = get_db_connection()
    c = conn.cursor()
    exists = c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not exists:
        r = role if role else 'guest'
        c.execute("INSERT INTO users (user_id, username, full_name, role) VALUES (?, ?, ?, ?)",
                  (user_id, username, full_name, r))
    else:
        if role:
            c.execute("UPDATE users SET role = ?, username = ?, full_name = ? WHERE user_id = ?",
                      (role, username, full_name, user_id))
        else:
            c.execute("UPDATE users SET username = ?, full_name = ? WHERE user_id = ?",
                      (username, full_name, user_id))
    conn.commit()
    conn.close()


def db_get_user(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def db_update_address(user_id, address):
    conn = get_db_connection()
    conn.execute("UPDATE users SET last_address = ? WHERE user_id = ?", (address, user_id))
    conn.commit()
    conn.close()


# --- Orders ---
def db_create_order(data):
    conn = get_db_connection()
    cur = conn.cursor()
    items_str = ", ".join(data['items'])
    cur.execute('''INSERT INTO orders 
                   (client_id, shop_type, items, addr_to, goods_price, delivery_price, total_price, status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (data['client_id'], data['shop_type'], items_str, data['addr_to'],
                 data['goods_price'], data['delivery_price'], data['total_price'], data['status']))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def db_get_orders(status=None, client_id=None, courier_id=None):
    conn = get_db_connection()
    query = "SELECT * FROM orders WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if client_id:
        query += " AND client_id = ?"
        params.append(client_id)
    if courier_id:
        query += " AND courier_id = ?"
        params.append(courier_id)
    query += " ORDER BY id DESC LIMIT 20"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def db_get_order(order_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    return row


def db_update_order_status(order_id, status, courier_id=None):
    conn = get_db_connection()
    if courier_id:
        conn.execute("UPDATE orders SET status = ?, courier_id = ? WHERE id = ?", (status, courier_id, order_id))
    else:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()


# ==============================================================================
# STATES & CONSTANTS
# ==============================================================================

STATUS_CREATED = "🆕 Создан"
STATUS_ASSIGNED = "🏃 Курьер выехал"
STATUS_BOUGHT = "🛍 Курьер купил товары"
STATUS_ON_WAY = "🚚 Курьер едет к вам"
STATUS_DELIVERED = "✅ Доставлен"
STATUS_CANCELLED = "❌ Отменен"

(ORDER_SHOP, ORDER_ITEMS, ORDER_ADDRESS, ORDER_CONFIRM) = range(4)


# ==============================================================================
# HELPERS
# ==============================================================================

def get_role(user_id):
    if user_id in ADMIN_IDS: return "admin"
    if user_id in APPROVED_COURIERS: return "courier"
    user = db_get_user(user_id)
    return user['role'] if user else "guest"


async def send_or_edit(update: Update, text: str, reply_markup=None):
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"UI Error: {e}")


def get_main_menu_keyboard(role):
    keyboard = []
    if role == "client":
        keyboard = [
            [InlineKeyboardButton("🛍 В магазин", callback_data="menu_create_order")],
            [InlineKeyboardButton("📦 История", callback_data="menu_my_orders"),
             InlineKeyboardButton("👤 Профиль", callback_data="menu_profile")],
            [InlineKeyboardButton("🔍 Отследить", callback_data="menu_track"),
             InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
        ]
    elif role == "courier":
        keyboard = [
            [InlineKeyboardButton("📋 Лента заказов", callback_data="courier_market")],
            [InlineKeyboardButton("📦 В работе", callback_data="courier_active")],
            [InlineKeyboardButton("💰 Доход", callback_data="courier_stats"),
             InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
        ]
    elif role == "admin":
        keyboard = [[InlineKeyboardButton("📋 Все заказы", callback_data="admin_all_orders")]]
    else:
        keyboard = [
            [InlineKeyboardButton("👤 Я Заказчик", callback_data="role_client")],
            [InlineKeyboardButton("🚴 Я Курьер", callback_data="role_courier_start")],
        ]
    return InlineKeyboardMarkup(keyboard)


# ==============================================================================
# HANDLERS
# ==============================================================================

async def post_init(application: Application):
    init_db()
    await application.bot.set_my_commands([("start", "🏠 Меню"), ("help", "❓ Справка")])
    await application.bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="Сервис", web_app=WebAppInfo(url=WEB_APP_URL))
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_upsert_user(user.id, user.username, user.full_name)
    try:
        await context.bot.set_chat_menu_button(
            chat_id=update.effective_chat.id,
            menu_button=MenuButtonWebApp(text="Сервис", web_app=WebAppInfo(url=WEB_APP_URL))
        )
    except:
        pass

    role = get_role(user.id)
    text = f"👋 Привет, {user.first_name}!\nДобро пожаловать в **FastBox Market**."
    if role == "guest": text = "👋 Добро пожаловать! Как вы хотите использовать бота?"

    await update.message.reply_text(text, reply_markup=get_main_menu_keyboard(role))


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    # Смена роли на Клиента
    if query.data == "role_client":
        db_upsert_user(user.id, user.username, user.full_name, "client")
        await query.edit_message_text("✅ Аккаунт клиента создан!", reply_markup=get_main_menu_keyboard("client"))
        return

    # Смена роли на Курьера
    if query.data == "role_courier_start":
        db_upsert_user(user.id, user.username, user.full_name, "courier")
        await query.edit_message_text("🚴 Вы стали Курьером! Ожидайте заказов.",
                                      reply_markup=get_main_menu_keyboard("courier"))
        return

    if query.data == "main_menu":
        role = get_role(user.id)
        await query.edit_message_text(f"🏠 Главное меню ({role}):", reply_markup=get_main_menu_keyboard(role))


# --- SHOPPING FLOW ---

async def start_create_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    context.user_data['cart'] = []
    context.user_data['cart_price'] = 0
    kb = []
    for key, val in CATALOGS.items():
        kb.append([InlineKeyboardButton(val['name'], callback_data=f"shop_{key}")])
    kb.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_order")])
    await send_or_edit(update, "🏪 **Выберите магазин:**", InlineKeyboardMarkup(kb))
    return ORDER_SHOP


async def shop_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel_order":
        await query.edit_message_text("❌ Заказ отменен", reply_markup=get_main_menu_keyboard("client"))
        return ConversationHandler.END
    shop_key = query.data.split("_")[1]
    context.user_data['current_shop'] = shop_key
    await render_catalog(query, context, CATALOGS[shop_key])
    return ORDER_ITEMS


async def render_catalog(query, context, shop):
    cart = context.user_data.get('cart', [])
    total_goods = context.user_data.get('cart_price', 0)
    text = f"🏪 **{shop['name']}**\nВыберите товары:\n\n"
    if cart:
        text += "🛒 **В корзине:**\n" + "\n".join([f"- {item}" for item in cart])
        text += f"\n\n💰 Итого: **{total_goods} ₸**"
    else:
        text += "🛒 Корзина пуста"

    kb = []
    for item_name, price in shop['items'].items():
        kb.append([InlineKeyboardButton(f"{item_name} - {price} ₸", callback_data=f"add_{item_name}")])

    ctrl = []
    if cart: ctrl.append(InlineKeyboardButton("✅ Оформить", callback_data="cart_done"))
    ctrl.append(InlineKeyboardButton("🧹 Очистить", callback_data="cart_clear"))
    kb.append(ctrl)
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_shops")])

    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    except:
        pass


async def cart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    shop = CATALOGS[context.user_data['current_shop']]

    if data == "back_shops": return await start_create_order(update, context)
    if data == "cart_clear":
        context.user_data['cart'] = []
        context.user_data['cart_price'] = 0
        await render_catalog(query, context, shop)
        return ORDER_ITEMS

    if data == "cart_done":
        user = db_get_user(query.from_user.id)
        last_addr = user['last_address']
        text = "📍 **Куда доставить?**\nВведите адрес."
        kb = None
        if last_addr:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"🏠 {last_addr}", callback_data="use_last_addr")]])
            text += "\nИли выберите сохраненный:"
        await query.edit_message_text(text, reply_markup=kb)
        return ORDER_ADDRESS

    item_name = data.replace("add_", "")
    price = shop['items'].get(item_name, 0)
    context.user_data['cart'].append(item_name)
    context.user_data['cart_price'] += price
    await render_catalog(query, context, shop)
    return ORDER_ITEMS


async def order_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == "use_last_addr":
        user = db_get_user(update.effective_user.id)
        addr = user['last_address']
        await update.callback_query.answer()
    else:
        addr = update.message.text

    context.user_data['addr_to'] = addr
    cart_price = context.user_data['cart_price']
    delivery_price = 1000
    total = cart_price + delivery_price

    shop_name = CATALOGS[context.user_data['current_shop']]['name']
    items_list = "\n".join([f"• {i}" for i in context.user_data['cart']])

    summary = (f"🧾 **Подтверждение**\n🏪 {shop_name}\n🛒 {items_list}\n📍 {addr}\n"
               f"💰 Товары: {cart_price} + Доставка: {delivery_price} = **{total} ₸**")
    kb = [[InlineKeyboardButton("✅ Заказать", callback_data="confirm_yes"),
           InlineKeyboardButton("❌ Отмена", callback_data="confirm_no")]]

    if update.callback_query:
        await update.callback_query.edit_message_text(summary, reply_markup=InlineKeyboardMarkup(kb),
                                                      parse_mode="Markdown")
    else:
        await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    context.user_data['final_order'] = {
        'client_id': update.effective_user.id,
        'shop_type': shop_name, 'items': context.user_data['cart'], 'addr_to': addr,
        'goods_price': cart_price, 'delivery_price': delivery_price, 'total_price': total, 'status': STATUS_CREATED
    }
    return ORDER_CONFIRM


async def order_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "confirm_no":
        await query.edit_message_text("❌ Заказ отменен", reply_markup=get_main_menu_keyboard("client"))
        return ConversationHandler.END

    order_data = context.user_data['final_order']
    oid = db_create_order(order_data)
    db_update_address(order_data['client_id'], order_data['addr_to'])
    await query.edit_message_text(f"✅ **Заказ #{oid} принят!**", reply_markup=get_main_menu_keyboard("client"))
    return ConversationHandler.END


# --- COURIER FLOW ---

async def courier_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    orders = db_get_orders(status=STATUS_CREATED)
    if not orders:
        await send_or_edit(update, "📭 Активных заказов нет.", get_main_menu_keyboard("courier"))
        return
    kb = []
    for o in orders:
        kb.append([InlineKeyboardButton(f"#{o['id']} {o['shop_type']} (+{o['delivery_price']}₸)",
                                        callback_data=f"courier_view_{o['id']}")])
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])
    await send_or_edit(update, "📋 **Доступные заказы:**", InlineKeyboardMarkup(kb))


async def courier_view_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    oid = int(query.data.split("_")[2])
    o = db_get_order(oid)
    if not o or o['status'] != STATUS_CREATED:
        await query.edit_message_text("❌ Заказ недоступен.", reply_markup=get_main_menu_keyboard("courier"))
        return
    text = (f"📦 **Заказ #{o['id']}**\n🏪 {o['shop_type']}\n🛒 {o['items']}\n📍 {o['addr_to']}\n\n"
            f"💵 Выкуп: {o['goods_price']} ₸\n💰 **Доход: {o['delivery_price']} ₸**")
    kb = [[InlineKeyboardButton("✅ Взять в работу", callback_data=f"courier_take_{o['id']}"),
           InlineKeyboardButton("⬅️ Назад", callback_data="courier_market")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))


async def courier_take_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    oid = int(query.data.split("_")[2])
    db_update_order_status(oid, STATUS_ASSIGNED, courier_id=query.from_user.id)
    await query.edit_message_text("✅ Заказ взят!", reply_markup=get_main_menu_keyboard("courier"))


async def courier_active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    uid = update.effective_user.id
    orders = get_db_connection().execute("SELECT * FROM orders WHERE courier_id = ? AND status != ?",
                                         (uid, STATUS_DELIVERED)).fetchall()
    if not orders:
        await send_or_edit(update, "Нет активных заказов.", get_main_menu_keyboard("courier"))
        return
    o = orders[0]
    flow = [STATUS_ASSIGNED, STATUS_BOUGHT, STATUS_ON_WAY, STATUS_DELIVERED]
    try:
        idx = flow.index(o['status'])
        if idx + 1 < len(flow):
            next_s = flow[idx + 1]
            btn_txt = "➡️ Следующий этап"
            if next_s == STATUS_BOUGHT:
                btn_txt = "🛍 Купил товары"
            elif next_s == STATUS_ON_WAY:
                btn_txt = "🚚 Еду к клиенту"
            elif next_s == STATUS_DELIVERED:
                btn_txt = "✅ Вручил"
            kb = [[InlineKeyboardButton(btn_txt, callback_data=f"status_upd_{o['id']}_{next_s}")],
                  [InlineKeyboardButton("⬅️ Меню", callback_data="main_menu")]]
            await send_or_edit(update,
                               f"🔥 **В работе #{o['id']}**\nСтатус: {o['status']}\n\n🛒 {o['items']}\n📍 {o['addr_to']}",
                               InlineKeyboardMarkup(kb))
        else:
            await send_or_edit(update, "Заказ завершен.", get_main_menu_keyboard("courier"))
    except:
        await send_or_edit(update, "Ошибка статуса.", get_main_menu_keyboard("courier"))


async def status_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    oid = int(parts[2])
    status = parts[3]
    db_update_order_status(oid, status)
    if status == STATUS_DELIVERED:
        await query.edit_message_text("🎉 Заказ завершен!", reply_markup=get_main_menu_keyboard("courier"))
    else:
        await courier_active(update, context)


# --- OTHER ---
async def client_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    orders = db_get_orders(client_id=update.effective_user.id)
    text = "📦 **История:**\n"
    if not orders: text = "📭 Пусто"
    for o in orders: text += f"🔹 #{o['id']} {o['shop_type']} ({o['total_price']}₸) - {o['status']}\n"
    await send_or_edit(update, text,
                       InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Меню", callback_data="main_menu")]]))


async def courier_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    conn = get_db_connection()
    res = conn.execute("SELECT count(*), sum(delivery_price) FROM orders WHERE courier_id = ? AND status = ?",
                       (update.effective_user.id, STATUS_DELIVERED)).fetchone()
    conn.close()
    await send_or_edit(update, f"💰 **Доход:**\nВыполнено: {res[0] or 0}\nЗаработано: {res[1] or 0} ₸",
                       InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Меню", callback_data="main_menu")]]))


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    await send_or_edit(update, "ℹ️ Маркетплейс доставки.",
                       InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Меню", callback_data="main_menu")]]))


async def user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    user = db_get_user(update.effective_user.id)
    await send_or_edit(update, f"👤 {user['full_name']}\nРоль: {user['role']}",
                       InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Меню", callback_data="main_menu")]]))


async def admin_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    orders = db_get_orders()
    text = "📋 **Все заказы:**\n"
    for o in orders: text += f"#{o['id']} {o['shop_type']} -> {o['status']}\n"
    await send_or_edit(update, text,
                       InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Меню", callback_data="main_menu")]]))


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    app = Application.builder().token(API_TOKEN).post_init(post_init).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_create_order, pattern="^menu_create_order$")],
        states={
            ORDER_SHOP: [CallbackQueryHandler(shop_catalog, pattern="^shop_"),
                         CallbackQueryHandler(shop_catalog, pattern="^cancel_order$")],
            ORDER_ITEMS: [CallbackQueryHandler(cart_handler, pattern="^add_|^cart_|^back_")],
            ORDER_ADDRESS: [MessageHandler(filters.TEXT, order_address),
                            CallbackQueryHandler(order_address, pattern="^use_last_addr$")],
            ORDER_CONFIRM: [CallbackQueryHandler(order_confirm, pattern="^confirm_")]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$|^role_client$|^role_courier_start$"))
    app.add_handler(CallbackQueryHandler(client_my_orders, pattern="^menu_my_orders$"))
    app.add_handler(CallbackQueryHandler(user_profile, pattern="^menu_profile$"))
    app.add_handler(CallbackQueryHandler(help_handler, pattern="^menu_help$"))

    app.add_handler(CallbackQueryHandler(courier_market, pattern="^courier_market$"))
    app.add_handler(CallbackQueryHandler(courier_view_order, pattern="^courier_view_"))
    app.add_handler(CallbackQueryHandler(courier_take_order, pattern="^courier_take_"))
    app.add_handler(CallbackQueryHandler(courier_active, pattern="^courier_active$"))
    app.add_handler(CallbackQueryHandler(status_update, pattern="^status_upd_"))
    app.add_handler(CallbackQueryHandler(courier_stats, pattern="^courier_stats$"))
    app.add_handler(CallbackQueryHandler(admin_all_orders, pattern="^admin_all_orders$"))

    print("Market Bot Started...")
    app.run_polling()


if __name__ == "__main__":
    main()