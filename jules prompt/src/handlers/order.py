from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from src.database import Database

db = Database()

(
    TYPE,
    CITY,
    SENDER_ADDRESS,
    RECEIVER_ADDRESS,
    RECEIVER_PHONE,
    COMMENT,
    WEIGHT,
    DELIVERY_DATE,
    DELIVERY_TIME,
    CONFIRMATION
) = range(10)

async def create_order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Вещи", "Еда", "Продукты", "Лекарства"]]
    
    await update.message.reply_text(
        "Начнем оформление заказа.\n"
        "Что вы хотите отправить?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return TYPE

async def order_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data['type'] = update.message.text
    
    await update.message.reply_text(
        "Укажите город/регион доставки (например, Алматы):",
        reply_markup=ReplyKeyboardRemove(),
    )
    return CITY

async def order_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data['city'] = update.message.text
    
    await update.message.reply_text(
        "Введите адрес отправителя (откуда забрать):"
    )
    return SENDER_ADDRESS

async def sender_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data['sender_address'] = update.message.text
    
    await update.message.reply_text(
        "Введите адрес получателя (куда доставить):"
    )
    return RECEIVER_ADDRESS

async def receiver_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data['receiver_address'] = update.message.text
    
    await update.message.reply_text(
        "Введите контакты получателя (телефон/имя):"
    )
    return RECEIVER_PHONE

async def receiver_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data['receiver_phone'] = update.message.text
    
    await update.message.reply_text(
        "Добавьте комментарий к заказу (подъезд, код двери, этаж и т.д.) или напишите 'Нет':"
    )
    return COMMENT

async def comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data['comment'] = update.message.text
    
    reply_keyboard = [["Маленькая (до 5 кг)", "Средняя (5-20 кг)", "Большая (20+ кг)"]]
    await update.message.reply_text(
        "Укажите вес/габариты посылки:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return WEIGHT

async def weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data['weight'] = update.message.text
    
    reply_keyboard = [["Сегодня", "Завтра", "Послезавтра"]]
    await update.message.reply_text(
        "Выберите дату доставки:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return DELIVERY_DATE

async def delivery_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data['delivery_date'] = update.message.text
    
    reply_keyboard = [["09:00-13:00", "14:00-18:00", "19:00-22:00"]]
    await update.message.reply_text(
        "Выберите удобное время:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return DELIVERY_TIME

def calculate_price(data):
    # Mock calculation logic
    base_price = 1000
    
    city = data.get('city', '').lower()
    
    # Inter-city logic (Simple mock)
    # If the city is different from a base city (e.g. Almaty), add cost
    # For now, just check if it's NOT Almaty
    if "алматы" not in city and "almaty" not in city:
        base_price += 2000  # Inter-city surcharge
    
    if "Средняя" in data.get('weight', ''):
        base_price += 500
    elif "Большая" in data.get('weight', ''):
        base_price += 1500
        
    if data.get('type') == "Лекарства":
        base_price += 200 # Extra care handling
        
    return base_price

async def delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data['delivery_time'] = update.message.text
    
    price = calculate_price(user_data)
    user_data['price'] = price
    
    summary = (
        f"Пожалуйста, проверьте данные заказа:\n\n"
        f"Тип: {user_data['type']}\n"
        f"Город: {user_data['city']}\n"
        f"Откуда: {user_data['sender_address']}\n"
        f"Куда: {user_data['receiver_address']}\n"
        f"Получатель: {user_data['receiver_phone']}\n"
        f"Комментарий: {user_data['comment']}\n"
        f"Вес: {user_data['weight']}\n"
        f"Дата: {user_data['delivery_date']}\n"
        f"Время: {user_data['delivery_time']}\n\n"
        f"💰 Ориентировочная стоимость: {price} ₸\n\n"
        f"Всё верно?"
    )
    
    reply_keyboard = [["Да", "Нет, отменить"]]
    await update.message.reply_text(
        summary,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRMATION

async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    user = update.effective_user
    
    if answer == "Да":
        # Save to DB
        order_id = await db.add_order(user.id, context.user_data)
        
        main_keyboard = [
            ["Создать заказ", "Мои заказы"],
            ["Поддержка"]
        ]
        
        await update.message.reply_text(
            f"Заказ #{order_id} успешно создан! Мы начали поиск курьера.",
            reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
        )
        context.user_data.clear()
        return ConversationHandler.END
    else:
        main_keyboard = [
            ["Создать заказ", "Мои заказы"],
            ["Поддержка"]
        ]
        await update.message.reply_text(
            "Оформление заказа отменено.",
            reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
        )
        context.user_data.clear()
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    main_keyboard = [
        ["Создать заказ", "Мои заказы"],
        ["Поддержка"]
    ]
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    )
    context.user_data.clear()
    return ConversationHandler.END

order_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^Создать заказ$"), create_order_start)],
    states={
        TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_type)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_city)],
        SENDER_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, sender_address)],
        RECEIVER_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receiver_address)],
        RECEIVER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receiver_phone)],
        COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, comment)],
        WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight)],
        DELIVERY_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delivery_date)],
        DELIVERY_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, delivery_time)],
        CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmation)],
    },
    fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^Отмена$"), cancel)],
)
