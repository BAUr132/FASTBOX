import logging
import datetime
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
# НАСТРОЙКИ КОНФИГУРАЦИИ
# ==============================================================================

# 1. Токен
API_TOKEN = "8571414658:AAG3-A-zzxoBIqxt9FqGewSKViHk5rSCtg0"

# 2. Ваш Telegram ID
ADMIN_IDS = [123456789]

# 3. Список ID утвержденных курьеров
APPROVED_COURIERS = []

# 4. Ссылка на ваше Web App
# Важно: URL должен быть точным. Если в браузере работает, значит всё ок.
WEB_APP_URL = "https://baur132.github.io/FASTBOX/index.html"

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
courier_applications = {}

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


async def send_or_edit(update: Update, text: str, reply_markup=None):
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")


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
            [InlineKeyboardButton("📦 Активные заказы", callback_data="courier_active")],
            [InlineKeyboardButton("💰 Статистика", callback_data="courier_stats"),
             InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
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


def get_reply_keyboard(role):
    if role == "client":
        return ReplyKeyboardMarkup([
            ["➕ Создать заказ", "📦 Мои заказы"],
            ["🔍 Отследить", "❓ Помощь"],
        ], resize_keyboard=True)
    elif role == "courier":
        return ReplyKeyboardMarkup([
            ["📋 Доступные заказы", "📦 Активные заказы"],
            ["💰 Статистика", "❓ Помощь"],
        ], resize_keyboard=True)
    elif role == "admin":
        return ReplyKeyboardMarkup([
            ["📋 Все заказы", "🚴 Заявки курьеров"],
            ["⚙️ Настройки", "❓ Помощь"],
        ], resize_keyboard=True)
    else:
        return None


# ==============================================================================
# ОБЩАЯ ЛОГИКА
# ==============================================================================

async def post_init(application: Application):
    """
    Устанавливает кнопку "по умолчанию" для новых пользователей.
    """
    await application.bot.set_my_commands([
        ("start", "🏠 Главное меню / Перезапуск"),
        ("help", "❓ Справка"),
    ])

    # Установка глобальной кнопки (может обновляться с задержкой у старых юзеров)
    await application.bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="Сервис", web_app=WebAppInfo(url=WEB_APP_URL))
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # --- ВАЖНОЕ ИСПРАВЛЕНИЕ ---
    # Принудительно обновляем кнопку ЛИЧНО для этого пользователя.
    # Это решает проблему "кнопка не появилась".
    try:
        await context.bot.set_chat_menu_button(
            chat_id=update.effective_chat.id,
            menu_button=MenuButtonWebApp(text="Сервис", web_app=WebAppInfo(url=WEB_APP_URL))
        )
    except Exception as e:
        logger.error(f"Не удалось обновить кнопку меню: {e}")
    # --------------------------

    role = get_role(user.id)

    if user.id not in users_db and role != "admin":
        users_db[user.id] = {"role": "guest", "name": user.full_name, "username": user.username}

    text = f"Добро пожаловать в FastBox, {user.first_name}!\nВаша роль: {role.upper()}"
    if role == "guest":
        text = "Добро пожаловать в FastBox! Выберите, кто вы:"

    await update.message.reply_text(text, reply_markup=get_main_menu_keyboard(role))

    reply_kb = get_reply_keyboard(role)
    if reply_kb:
        await update.message.reply_text("⌨️ Меню обновлено", reply_markup=reply_kb)


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in users_db and user_id not in ADMIN_IDS:
        users_db[user_id] = {"role": "guest", "name": query.from_user.full_name, "username": query.from_user.username}

    role = get_role(user_id)

    if query.data == "role_client":
        users_db[user_id]["role"] = "client"
        await query.edit_message_text("✅ Вы зарегистрированы как Клиент!",
                                      reply_markup=get_main_menu_keyboard("client"))
        await context.bot.send_message(chat_id=user_id, text="👇 Пользуйтесь кнопками внизу",
                                       reply_markup=get_reply_keyboard("client"))
        return

    if query.data == "main_menu":
        await query.edit_message_text(f"Главное меню ({role}):", reply_markup=get_main_menu_keyboard(role))


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()

    text = (
        "❓ **Справка FastBox**\n\n"
        "**Клиенту:**\n"
        "— 'Создать заказ': заполните анкету.\n"
        "— 'Мои заказы': список ваших отправлений.\n\n"
        "**Курьеру:**\n"
        "— 'Доступные': общая лента заказов.\n"
        "— 'Активные': заказы в работе.\n\n"
        "**Mini App:**\n"
        "Нажмите кнопку 'Сервис' слева от поля ввода текста."
    )
    kb = [[InlineKeyboardButton("⬅️ В меню", callback_data="main_menu")]]
    await send_or_edit(update, text, InlineKeyboardMarkup(kb))


async def mini_app_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚧 **Mini App**\n\n"
        "Используйте кнопку **'Сервис'** слева внизу (рядом с полем ввода), чтобы открыть приложение.",
        parse_mode="Markdown"
    )


# ==============================================================================
# ФУНКЦИОНАЛ КЛИЕНТА
# ==============================================================================

async def start_create_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()

    keyboard = [
        [InlineKeyboardButton("🍔 Еда", callback_data="type_Food"),
         InlineKeyboardButton("📦 Вещи", callback_data="type_Items")],
        [InlineKeyboardButton("📄 Документы", callback_data="type_Docs"),
         InlineKeyboardButton("💊 Лекарства", callback_data="type_Meds")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_order")]
    ]
    await send_or_edit(update, "Шаг 1/7. Что доставляем?", InlineKeyboardMarkup(keyboard))
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
    if update.callback_query: await update.callback_query.answer()
    user_id = update.effective_user.id

    user_orders = [o for o in orders_db.values() if o.get('client_id') == user_id]

    if not user_orders:
        await send_or_edit(update, "У вас нет заказов.", get_main_menu_keyboard("client"))
        return
    text = "📦 **Ваши заказы:**\n" + "\n".join(
        [f"#{o.get('id')} - {STATUS_TRANSLATION.get(o.get('status'), 'Unknown')}" for o in user_orders[-5:]])
    await send_or_edit(update, text,
                       InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]))


async def client_track_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    user_id = update.effective_user.id

    user_orders = [o for o in orders_db.values() if
                   o.get('client_id') == user_id and o.get('status') != STATUS_DELIVERED]
    if not user_orders:
        await send_or_edit(update, "Нет активных заказов для отслеживания.", get_main_menu_keyboard("client"))
        return
    text = "🔍 **Трекинг (Активные):**\n\n"
    for o in user_orders:
        text += f"📦 **#{o.get('id')}**: {STATUS_TRANSLATION.get(o.get('status'), 'Unknown')}\n📍 {o.get('city_to')}\n\n"
    await send_or_edit(update, text,
                       InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]))


# ==============================================================================
# ФУНКЦИОНАЛ КУРЬЕРА
# ==============================================================================

async def start_courier_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    await send_or_edit(update, "Введите ФИО:")
    return COURIER_REG_NAME


async def courier_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['courier_app'] = {'name': update.message.text, 'id': update.effective_user.id}
    await update.message.reply_text("Ваш город:")
    return COURIER_REG_CITY


async def courier_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['courier_app']['city'] = update.message.text
    await update.message.reply_text("Телефон:")
    return COURIER_REG_CITY


async def courier_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['courier_app']['phone'] = update.message.text
    await update.message.reply_text("Транспорт:")
    return COURIER_REG_TRANSPORT


async def courier_transport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    app_data = context.user_data['courier_app']
    app_data['transport'] = update.message.text
    courier_applications[app_data['id']] = app_data

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
    if update.callback_query: await update.callback_query.answer()

    orders = [o for o in orders_db.values() if o.get('status') == STATUS_CREATED]
    if not orders:
        await send_or_edit(update, "Нет доступных заказов.", get_main_menu_keyboard("courier"))
        return
    kb = [[InlineKeyboardButton(f"#{o['id']} {o['city_from']}->{o['city_to']} ({o['price']})",
                                callback_data=f"courier_view_{o['id']}")] for o in orders]
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])
    await send_or_edit(update, "Доступные заказы:", InlineKeyboardMarkup(kb))


async def courier_view_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        oid = int(query.data.split("_")[2])
        o = orders_db.get(oid)
        if not o or o.get('status') != STATUS_CREATED:
            await query.edit_message_text("Заказ недоступен (возможно, уже взят).",
                                          reply_markup=get_main_menu_keyboard("courier"))
            return
        text = f"📦 Заказ #{oid}\n{o['type']}\n{o['city_from']} -> {o['city_to']}\nВес: {o['weight']}\n💰 {o['price']}"
        kb = [[InlineKeyboardButton("✅ Взять", callback_data=f"courier_take_{oid}"),
               InlineKeyboardButton("⬅️ Назад", callback_data="courier_market")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    except Exception as e:
        logger.error(f"Error viewing order: {e}")
        await query.edit_message_text("Ошибка доступа к заказу.", reply_markup=get_main_menu_keyboard("courier"))


async def courier_take_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        oid = int(query.data.split("_")[2])
        if oid not in orders_db:
            await query.edit_message_text("Ошибка: Заказ не найден в базе.",
                                          reply_markup=get_main_menu_keyboard("courier"))
            return

        orders_db[oid]['status'] = STATUS_ASSIGNED
        orders_db[oid]['courier_id'] = query.from_user.id
        await query.edit_message_text("✅ Вы взяли заказ! См. 'Активные'",
                                      reply_markup=get_main_menu_keyboard("courier"))
    except Exception as e:
        logger.error(f"Error taking order: {e}")


async def courier_active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()

    user_id = update.effective_user.id

    # ИСПРАВЛЕНИЕ: Безопасное получение данных
    orders = []
    for o in orders_db.values():
        if o.get('courier_id') == user_id and o.get('status') != STATUS_DELIVERED:
            orders.append(o)

    if not orders:
        await send_or_edit(update, "Нет активных заказов.", get_main_menu_keyboard("courier"))
        return

    o = orders[0]
    statuses = [STATUS_ASSIGNED, STATUS_TO_SENDER, STATUS_PICKED_UP, STATUS_TO_RECEIVER, STATUS_DELIVERED]
    try:
        current_status = o.get('status')
        if current_status not in statuses:
            await send_or_edit(update, f"Неизвестный статус заказа #{o['id']}", get_main_menu_keyboard("courier"))
            return

        idx = statuses.index(current_status)
        if idx + 1 < len(statuses):
            next_s = statuses[idx + 1]
            btn_text = "➡️ Следующий статус"
            if next_s == STATUS_TO_SENDER: btn_text = "Прибыл к отправителю"
            if next_s == STATUS_PICKED_UP: btn_text = "Забрал посылку"
            if next_s == STATUS_TO_RECEIVER: btn_text = "Еду к получателю"
            if next_s == STATUS_DELIVERED: btn_text = "✅ Вручил"

            kb = [[InlineKeyboardButton(btn_text, callback_data=f"status_upd_{o['id']}_{next_s}")],
                  [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]
            await send_or_edit(update, f"В работе #{o['id']}\nСтатус: {STATUS_TRANSLATION.get(current_status)}",
                               InlineKeyboardMarkup(kb))
        else:
            await send_or_edit(update, "Заказ уже завершен.", get_main_menu_keyboard("courier"))
    except Exception as e:
        logger.error(f"Error in courier_active: {e}")
        await send_or_edit(update, "Ошибка обработки заказа.", get_main_menu_keyboard("courier"))


async def status_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, _, oid_str, status = query.data.split("_")
    oid = int(oid_str)

    if oid in orders_db:
        orders_db[oid]['status'] = status
        if status == STATUS_DELIVERED:
            await query.edit_message_text("Заказ выполнен!", reply_markup=get_main_menu_keyboard("courier"))
        else:
            await courier_active(update, context)
    else:
        await query.edit_message_text("Ошибка: Заказ не найден.", reply_markup=get_main_menu_keyboard("courier"))


async def courier_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    user_id = update.effective_user.id

    delivered = len(
        [o for o in orders_db.values() if o.get('courier_id') == user_id and o.get('status') == STATUS_DELIVERED])
    earnings = sum([o.get('price', 0) for o in orders_db.values() if
                    o.get('courier_id') == user_id and o.get('status') == STATUS_DELIVERED])

    text = f"📊 **Ваша статистика**\n\n✅ Доставлено заказов: {delivered}\n💰 Заработано: {earnings} KZT"
    kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]
    await send_or_edit(update, text, InlineKeyboardMarkup(kb))


def calculate_price(weight_category, city_from, city_to):
    # Простая логика цены для демонстрации
    base = 1000
    if city_from.lower() != city_to.lower():
        base += 2000  # Межгород

    if weight_category == ">10 кг":
        base += 1500
    elif weight_category == "5-10 кг":
        base += 1000
    elif weight_category == "1-5 кг":
        base += 500

    return base


# ==============================================================================
# ФУНКЦИОНАЛ АДМИНА
# ==============================================================================

async def admin_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()

    if not orders_db:
        text = "Список заказов пуст."
    else:
        text = "📋 **Все заказы системы:**\n" + "\n".join(
            [f"#{k} [{v.get('status')}] {v.get('city_from')}->{v.get('city_to')}" for k, v in orders_db.items()])

    kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]
    await send_or_edit(update, text, InlineKeyboardMarkup(kb))


async def admin_courier_apps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()

    text = "🚴 **Заявки курьеров:**\n\n"
    if not courier_applications:
        text += "Нет ожидающих заявок."
    else:
        for uid, app in courier_applications.items():
            if uid not in APPROVED_COURIERS:
                text += f"- {app['name']}, {app['city']} ({app['phone']})\n"
        text += "\n(Кнопки одобрения приходят в чат при подаче)"

    kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]
    await send_or_edit(update, text, InlineKeyboardMarkup(kb))


async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    text = "⚙️ **Настройки бота**\n\nТариф: Стандарт\nБазовая цена: 1000 KZT\nМежгород: +2000 KZT"
    kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]
    await send_or_edit(update, text, InlineKeyboardMarkup(kb))


async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action = query.data.split("_")[1]
    uid = int(query.data.split("_")[2])

    if action == "approve":
        APPROVED_COURIERS.append(uid)
        if uid in users_db: users_db[uid]['role'] = 'courier'
        await query.edit_message_text(f"✅ Курьер {uid} одобрен.")
        try:
            await context.bot.send_message(uid, "Вы приняты! Нажмите /start для обновления меню")
        except:
            pass
    else:
        await query.edit_message_text(f"❌ Курьер {uid} отклонен.")


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    application = Application.builder().token(API_TOKEN).post_init(post_init).build()

    # Клиент: Создание заказа
    order_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_create_order, pattern="^menu_create_order$"),
            MessageHandler(filters.Regex("^➕ Создать заказ$"), start_create_order)
        ],
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

    application.add_handler(CommandHandler("start", start))
    application.add_handler(order_conv)
    application.add_handler(courier_conv)

    # Общие
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$|^role_client$"))
    application.add_handler(CallbackQueryHandler(help_handler, pattern="^menu_help$"))
    application.add_handler(MessageHandler(filters.Regex("^❓ Помощь$"), help_handler))

    # NEW HANDLER (Mini Apps) - старая кнопка (можно удалить, если не нужна)
    application.add_handler(MessageHandler(filters.Regex("^📱 Mini Apps \(Скоро\)$"), mini_app_handler))

    # Клиент (Text + Inline triggers)
    application.add_handler(CallbackQueryHandler(client_my_orders, pattern="^menu_my_orders$"))
    application.add_handler(MessageHandler(filters.Regex("^📦 Мои заказы$"), client_my_orders))

    application.add_handler(CallbackQueryHandler(client_track_order, pattern="^menu_track$"))
    application.add_handler(MessageHandler(filters.Regex("^🔍 Отследить$"), client_track_order))

    # Курьер (Text + Inline triggers)
    application.add_handler(CallbackQueryHandler(courier_market, pattern="^courier_market$"))
    application.add_handler(MessageHandler(filters.Regex("^📋 Доступные заказы$"), courier_market))

    application.add_handler(CallbackQueryHandler(courier_active, pattern="^courier_active$"))
    application.add_handler(MessageHandler(filters.Regex("^📦 Активные заказы$"), courier_active))

    application.add_handler(CallbackQueryHandler(courier_stats, pattern="^courier_stats$"))
    application.add_handler(MessageHandler(filters.Regex("^💰 Статистика$"), courier_stats))

    # Смена статусов курьером
    application.add_handler(CallbackQueryHandler(courier_view_order, pattern="^courier_view_"))
    application.add_handler(CallbackQueryHandler(courier_take_order, pattern="^courier_take_"))
    application.add_handler(CallbackQueryHandler(status_update, pattern="^status_upd_"))

    # Админ
    application.add_handler(CallbackQueryHandler(admin_all_orders, pattern="^admin_all_orders$"))
    application.add_handler(MessageHandler(filters.Regex("^📋 Все заказы$"), admin_all_orders))

    application.add_handler(CallbackQueryHandler(admin_courier_apps, pattern="^admin_courier_apps$"))
    application.add_handler(MessageHandler(filters.Regex("^🚴 Заявки курьеров$"), admin_courier_apps))

    application.add_handler(CallbackQueryHandler(admin_settings, pattern="^admin_settings$"))
    application.add_handler(MessageHandler(filters.Regex("^⚙️ Настройки$"), admin_settings))

    application.add_handler(CallbackQueryHandler(admin_decision, pattern="^adm_"))

    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()