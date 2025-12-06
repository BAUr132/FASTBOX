import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
# НАСТРОЙКИ КОНФИГУРАЦИИ
# ==============================================================================

# 1. Вставьте сюда токен
API_TOKEN = "8571414658:AAG3-A-zzxoBIqxt9FqGewSKViHk5rSCtg0"

# 2. Вставьте сюда ваш Telegram ID (число)
ADMIN_IDS = [123456789]

# 3. Список ID утвержденных курьеров
APPROVED_COURIERS = []

# ==============================================================================
# ЛОГИРОВАНИЕ
# ==============================================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================================================================
# БАЗА ДАННЫХ (IN-MEMORY)
# ==============================================================================

users_db = {}
orders_db = {}
order_counter = 1
courier_applications = {}  # {user_id: {...data...}}

# Статусы
STATUS_CREATED = "CREATED"
STATUS_SCHEDULED = "SCHEDULED"
STATUS_ASSIGNED = "COURIER_ASSIGNED"
STATUS_TO_SENDER = "COURIER_TO_SENDER"
STATUS_PICKED_UP = "PICKED_UP"
STATUS_TO_RECEIVER = "COURIER_TO_RECEIVER"
STATUS_DELIVERED = "DELIVERED"
STATUS_CANCELLED = "CANCELLED"

STATUS_TRANSLATION = {
    STATUS_CREATED: "🆕 Ожидает курьера",
    STATUS_SCHEDULED: "🕒 Запланирован",
    STATUS_ASSIGNED: "🏃 Курьер назначен",
    STATUS_TO_SENDER: "🚶 Курьер едет к отправителю",
    STATUS_PICKED_UP: "📦 Посылка у курьера",
    STATUS_TO_RECEIVER: "🚚 Курьер едет к получателю",
    STATUS_DELIVERED: "✅ Доставлен",
    STATUS_CANCELLED: "❌ Отменен",
}

# Этапы разговора
(
    ORDER_TYPE,
    ORDER_CITY_FROM,
    ORDER_ADDR_FROM,
    ORDER_CITY_TO,
    ORDER_ADDR_TO,
    ORDER_WEIGHT,
    ORDER_TIME,
    ORDER_CONFIRM,
) = range(8)

(COURIER_REG_NAME, COURIER_REG_CITY, COURIER_REG_PHONE, COURIER_REG_TRANSPORT) = range(8, 12)


# ==============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==============================================================================

def get_role(user_id):
    if user_id in ADMIN_IDS:
        return "admin"
    if user_id in APPROVED_COURIERS:
        return "courier"
    user = users_db.get(user_id)
    if user:
        return user.get("role", "client")
    return "guest"


def get_main_menu_keyboard(role):
    keyboard = []
    if role == "client":
        keyboard = [
            [InlineKeyboardButton("➕ Создать заказ", callback_data="menu_create_order")],
            [InlineKeyboardButton("📦 Мои заказы", callback_data="menu_my_orders")],
            [InlineKeyboardButton("🔍 Отследить", callback_data="menu_track"),
             InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
        ]
    elif role == "courier":
        keyboard = [
            [InlineKeyboardButton("📋 Доступные заказы", callback_data="courier_market")],
            [InlineKeyboardButton("📦 Мои активные заказы", callback_data="courier_active")],
            [InlineKeyboardButton("💰 Моя статистика", callback_data="courier_stats")],
            [InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
        ]
    elif role == "admin":
        keyboard = [
            [InlineKeyboardButton("📋 Все заказы", callback_data="admin_all_orders")],
            [InlineKeyboardButton("🚴 Заявки курьеров", callback_data="admin_courier_apps")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("👤 Я Клиент", callback_data="role_client")],
            [InlineKeyboardButton("🚴 Я Курьер", callback_data="role_courier_start")],
        ]
    return InlineKeyboardMarkup(keyboard)


def calculate_price(weight_category, city_from, city_to):
    base = 1000
    if city_from.lower() != city_to.lower():
        base += 2000
    if weight_category == ">10 кг":
        base += 1500
    elif weight_category == "5-10 кг":
        base += 1000
    elif weight_category == "1-5 кг":
        base += 500
    return base


# ==============================================================================
# ОБЩАЯ ЛОГИКА (START / MENU / HELP)
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role = get_role(user.id)

    if user.id not in users_db and role != "admin":
        users_db[user.id] = {"role": "guest", "name": user.full_name, "username": user.username}

    text = f"Добро пожаловать в FastBox, {user.first_name}!\nВаша роль: {role.upper()}"
    if role == "guest":
        text = "Добро пожаловать в FastBox! Выберите, кто вы:"

    await update.message.reply_text(text, reply_markup=get_main_menu_keyboard(role))


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Восстановление пользователя при перезапуске бота
    if user_id not in users_db and user_id not in ADMIN_IDS:
        users_db[user_id] = {"role": "guest", "name": query.from_user.full_name, "username": query.from_user.username}

    role = get_role(user_id)

    if query.data == "role_client":
        users_db[user_id]["role"] = "client"
        await query.edit_message_text("Вы зарегистрированы как Клиент!", reply_markup=get_main_menu_keyboard("client"))
        return

    if query.data == "main_menu":
        await query.edit_message_text(f"Главное меню ({role}):", reply_markup=get_main_menu_keyboard(role))


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    role = get_role(query.from_user.id)
    text = (
        "❓ **Справка**\n\n"
        "**Клиенту:** Нажмите 'Создать заказ', заполните форму. Курьер возьмет заказ, и вы получите уведомление.\n"
        "**Курьеру:** 'Доступные заказы' - лента новых заказов. 'Активные' - те, что вы взяли в работу.\n"
        "**Админу:** Управление через меню."
    )
    kb = [[InlineKeyboardButton("⬅️ В меню", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


# ==============================================================================
# ФУНКЦИОНАЛ КЛИЕНТА
# ==============================================================================

# ... (Код создания заказа остался прежним, сокращаю для читаемости, в полном файле он будет) ...
async def start_create_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🍔 Еда", callback_data="type_Food"),
         InlineKeyboardButton("📦 Вещи", callback_data="type_Items")],
        [InlineKeyboardButton("📄 Документы", callback_data="type_Docs"),
         InlineKeyboardButton("💊 Лекарства", callback_data="type_Meds")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_order")]
    ]
    await query.edit_message_text("Шаг 1/7. Что доставляем?", reply_markup=InlineKeyboardMarkup(keyboard))
    return ORDER_TYPE


async def order_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel_order":
        await query.edit_message_text("Оформление отменено.", reply_markup=get_main_menu_keyboard("client"))
        return ConversationHandler.END
    context.user_data['new_order'] = {'type': query.data.split("_")[1]}
    await query.edit_message_text(f"Шаг 2/7. Введите **Город отправителя** (текстом):")
    return ORDER_CITY_FROM


async def order_city_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_order']['city_from'] = update.message.text
    await update.message.reply_text(f"Шаг 3/7. Введите **Адрес отправителя** (улица, дом):")
    return ORDER_ADDR_FROM


async def order_addr_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_order']['addr_from'] = update.message.text
    await update.message.reply_text("Шаг 4/7. Введите **Город получателя** (текстом):")
    return ORDER_CITY_TO


async def order_city_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_order']['city_to'] = update.message.text
    await update.message.reply_text(f"Шаг 5/7. Введите **Адрес получателя**:")
    return ORDER_ADDR_TO


async def order_addr_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_order']['addr_to'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("0-5 кг", callback_data="w_1-5"), InlineKeyboardButton(">5 кг", callback_data="w_>5")]]
    await update.message.reply_text("Шаг 6/7. Выберите вес:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ORDER_WEIGHT


async def order_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['new_order']['weight'] = query.data.split("_")[1]
    keyboard = [[InlineKeyboardButton("🚀 Срочно", callback_data="time_asap")]]
    await query.edit_message_text("Шаг 7/7. Срочность?", reply_markup=InlineKeyboardMarkup(keyboard))
    return ORDER_TIME


async def order_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = context.user_data['new_order']
    data['time_mode'] = 'asap'
    data['client_id'] = query.from_user.id
    data['price'] = calculate_price(data['weight'], data['city_from'], data['city_to'])

    summary = f"📋 **Подтверждение**\n{data['type']}, {data['city_from']} -> {data['city_to']}\n💰 {data['price']} KZT"
    kb = [[InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
           InlineKeyboardButton("❌ Нет", callback_data="confirm_no")]]
    await query.edit_message_text(summary, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    return ORDER_CONFIRM


async def order_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "confirm_no":
        await query.edit_message_text("Отменено.", reply_markup=get_main_menu_keyboard("client"))
        return ConversationHandler.END

    global order_counter
    data = context.user_data['new_order']
    data['id'] = order_counter
    data['status'] = STATUS_CREATED
    data['courier_id'] = None
    orders_db[order_counter] = data
    order_counter += 1

    await query.edit_message_text(f"✅ Заказ #{data['id']} создан!", reply_markup=get_main_menu_keyboard("client"))
    return ConversationHandler.END


async def client_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_orders = [o for o in orders_db.values() if o['client_id'] == query.from_user.id]
    if not user_orders:
        await query.edit_message_text("У вас нет заказов.", reply_markup=get_main_menu_keyboard("client"))
        return
    text = "📦 **Ваши заказы:**\n" + "\n".join(
        [f"#{o['id']} - {STATUS_TRANSLATION[o['status']]}" for o in user_orders[-5:]])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]), parse_mode="Markdown")


async def client_track_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Просто показываем активные заказы клиента с деталями
    user_orders = [o for o in orders_db.values() if
                   o['client_id'] == query.from_user.id and o['status'] != STATUS_DELIVERED]
    if not user_orders:
        await query.edit_message_text("Нет активных заказов для отслеживания.",
                                      reply_markup=get_main_menu_keyboard("client"))
        return
    text = "🔍 **Трекинг (Активные):**\n\n"
    for o in user_orders:
        text += f"📦 **#{o['id']}**: {STATUS_TRANSLATION[o['status']]}\n📍 {o['city_to']}\n\n"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]), parse_mode="Markdown")


# ==============================================================================
# ФУНКЦИОНАЛ КУРЬЕРА
# ==============================================================================

async def start_courier_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите ФИО:")
    return COURIER_REG_NAME


async def courier_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['courier_app'] = {'name': update.message.text, 'id': update.effective_user.id}
    await update.message.reply_text("Ваш город:")
    return COURIER_REG_CITY


async def courier_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['courier_app']['city'] = update.message.text
    await update.message.reply_text("Телефон:")
    return COURIER_REG_PHONE


async def courier_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['courier_app']['phone'] = update.message.text
    await update.message.reply_text("Транспорт:")
    return COURIER_REG_TRANSPORT


async def courier_transport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    app_data = context.user_data['courier_app']
    app_data['transport'] = update.message.text
    courier_applications[app_data['id']] = app_data

    # Уведомление админу
    for admin_id in ADMIN_IDS:
        try:
            kb = [[InlineKeyboardButton("✅ Одобрить", callback_data=f"adm_approve_{app_data['id']}"),
                   InlineKeyboardButton("❌ Отклонить", callback_data=f"adm_reject_{app_data['id']}")]]
            await context.bot.send_message(admin_id, f"🔔 Заявка курьера:\n{app_data['name']}",
                                           reply_markup=InlineKeyboardMarkup(kb))
        except:
            pass

    await update.message.reply_text("Заявка отправлена!")
    return ConversationHandler.END


async def courier_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    orders = [o for o in orders_db.values() if o['status'] == STATUS_CREATED]
    if not orders:
        await query.edit_message_text("Нет доступных заказов.", reply_markup=get_main_menu_keyboard("courier"))
        return
    kb = [[InlineKeyboardButton(f"#{o['id']} {o['city_from']}->{o['city_to']} ({o['price']})",
                                callback_data=f"courier_view_{o['id']}")] for o in orders]
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])
    await query.edit_message_text("Доступные заказы:", reply_markup=InlineKeyboardMarkup(kb))


async def courier_view_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    oid = int(query.data.split("_")[2])
    o = orders_db.get(oid)
    if not o or o['status'] != STATUS_CREATED:
        await query.edit_message_text("Заказ недоступен.", reply_markup=get_main_menu_keyboard("courier"))
        return
    text = f"📦 Заказ #{oid}\n{o['type']}\n{o['city_from']} -> {o['city_to']}\nВес: {o['weight']}\n💰 {o['price']}"
    kb = [[InlineKeyboardButton("✅ Взять", callback_data=f"courier_take_{oid}"),
           InlineKeyboardButton("⬅️ Назад", callback_data="courier_market")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))


async def courier_take_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    oid = int(query.data.split("_")[2])
    orders_db[oid]['status'] = STATUS_ASSIGNED
    orders_db[oid]['courier_id'] = query.from_user.id
    await query.edit_message_text("✅ Вы взяли заказ! См. 'Активные'", reply_markup=get_main_menu_keyboard("courier"))


async def courier_active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    orders = [o for o in orders_db.values() if
              o['courier_id'] == query.from_user.id and o['status'] != STATUS_DELIVERED]
    if not orders:
        await query.edit_message_text("Нет активных заказов.", reply_markup=get_main_menu_keyboard("courier"))
        return

    o = orders[0]  # Показываем первый
    statuses = [STATUS_ASSIGNED, STATUS_TO_SENDER, STATUS_PICKED_UP, STATUS_TO_RECEIVER, STATUS_DELIVERED]
    try:
        idx = statuses.index(o['status'])
        next_s = statuses[idx + 1]
        btn_text = "➡️ Следующий статус"
        if next_s == STATUS_TO_SENDER: btn_text = "Прибыл к отправителю"
        if next_s == STATUS_PICKED_UP: btn_text = "Забрал посылку"
        if next_s == STATUS_TO_RECEIVER: btn_text = "Еду к получателю"
        if next_s == STATUS_DELIVERED: btn_text = "✅ Вручил"

        kb = [[InlineKeyboardButton(btn_text, callback_data=f"status_upd_{o['id']}_{next_s}")],
              [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]
        await query.edit_message_text(f"В работе #{o['id']}\nСтатус: {STATUS_TRANSLATION[o['status']]}",
                                      reply_markup=InlineKeyboardMarkup(kb))
    except:
        await query.edit_message_text("Заказ завершен.", reply_markup=get_main_menu_keyboard("courier"))


async def status_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, _, oid, status = query.data.split("_")
    orders_db[int(oid)]['status'] = status
    if status == STATUS_DELIVERED:
        await query.edit_message_text("Заказ выполнен!", reply_markup=get_main_menu_keyboard("courier"))
    else:
        await courier_active(update, context)


async def courier_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Демонстрационная статистика
    delivered = len(
        [o for o in orders_db.values() if o['courier_id'] == query.from_user.id and o['status'] == STATUS_DELIVERED])
    earnings = sum([o['price'] for o in orders_db.values() if
                    o['courier_id'] == query.from_user.id and o['status'] == STATUS_DELIVERED])

    text = (
        f"📊 **Ваша статистика**\n\n"
        f"✅ Доставлено заказов: {delivered}\n"
        f"💰 Заработано: {earnings} KZT\n"
        f"⭐ Рейтинг: 5.0 (New)"
    )
    kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


# ==============================================================================
# ФУНКЦИОНАЛ АДМИНА
# ==============================================================================

async def admin_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not orders_db:
        text = "Список заказов пуст."
    else:
        text = "📋 **Все заказы системы:**\n" + "\n".join(
            [f"#{k} [{v['status']}] {v['city_from']}->{v['city_to']}" for k, v in orders_db.items()])

    kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def admin_courier_apps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "🚴 **Заявки курьеров:**\n\n"
    if not courier_applications:
        text += "Нет ожидающих заявок."
    else:
        for uid, app in courier_applications.items():
            if uid not in APPROVED_COURIERS:
                text += f"- {app['name']}, {app['city']} ({app['phone']})\n"
        text += "\n(Кнопки одобрения приходят в чат при подаче)"

    kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "⚙️ **Настройки бота**\n\nТариф: Стандарт\nБазовая цена: 1000 KZT\nМежгород: +2000 KZT"
    kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action = query.data.split("_")[1]
    uid = int(query.data.split("_")[2])

    if action == "approve":
        APPROVED_COURIERS.append(uid)
        if uid in users_db: users_db[uid]['role'] = 'courier'
        await query.edit_message_text(f"✅ Курьер {uid} одобрен.")
        try:
            await context.bot.send_message(uid, "Вы приняты! Нажмите /start")
        except:
            pass
    else:
        await query.edit_message_text(f"❌ Курьер {uid} отклонен.")


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    application = Application.builder().token(API_TOKEN).build()

    # Клиент: Создание заказа
    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_create_order, pattern="^menu_create_order$")],
        states={
            ORDER_TYPE: [CallbackQueryHandler(order_type, pattern="^type_.*"),
                         CallbackQueryHandler(order_type, pattern="^cancel_order$")],
            ORDER_CITY_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_city_from)],
            ORDER_ADDR_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_addr_from)],
            ORDER_CITY_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_city_to)],
            ORDER_ADDR_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_addr_to)],
            ORDER_WEIGHT: [CallbackQueryHandler(order_weight, pattern="^w_.*")],
            ORDER_TIME: [CallbackQueryHandler(order_time, pattern="^time_.*")],
            ORDER_CONFIRM: [CallbackQueryHandler(order_confirm, pattern="^confirm_.*")],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False
    )

    # Курьер: Регистрация
    courier_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_courier_reg, pattern="^role_courier_start$")],
        states={
            COURIER_REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, courier_name)],
            COURIER_REG_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, courier_city)],
            COURIER_REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, courier_phone)],
            COURIER_REG_TRANSPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, courier_transport)],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False
    )

    # --- РЕГИСТРАЦИЯ ХЕНДЛЕРОВ ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(order_conv)
    application.add_handler(courier_conv)

    # Общие
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$|^role_client$"))
    application.add_handler(CallbackQueryHandler(help_handler, pattern="^menu_help$"))

    # Клиент
    application.add_handler(CallbackQueryHandler(client_my_orders, pattern="^menu_my_orders$"))
    application.add_handler(CallbackQueryHandler(client_track_order, pattern="^menu_track$"))

    # Курьер
    application.add_handler(CallbackQueryHandler(courier_market, pattern="^courier_market$"))
    application.add_handler(CallbackQueryHandler(courier_view_order, pattern="^courier_view_"))
    application.add_handler(CallbackQueryHandler(courier_take_order, pattern="^courier_take_"))
    application.add_handler(CallbackQueryHandler(courier_active, pattern="^courier_active$"))
    application.add_handler(CallbackQueryHandler(status_update, pattern="^status_upd_"))
    application.add_handler(CallbackQueryHandler(courier_stats, pattern="^courier_stats$"))

    # Админ (ОТСУТСТВОВАЛИ В ПРОШЛОЙ ВЕРСИИ)
    application.add_handler(CallbackQueryHandler(admin_all_orders, pattern="^admin_all_orders$"))
    application.add_handler(CallbackQueryHandler(admin_courier_apps, pattern="^admin_courier_apps$"))
    application.add_handler(CallbackQueryHandler(admin_settings, pattern="^admin_settings$"))
    application.add_handler(CallbackQueryHandler(admin_decision, pattern="^adm_"))

    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()