from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler, CommandHandler
from src.database import Database

db = Database()

PHONE = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Check if we already have the phone number (optional optimization, but good for UX)
    # For now, we'll just ask for it to complete the registration flow as per requirements
    
    contact_keyboard = [[KeyboardButton("Отправить номер телефона", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(contact_keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Добро пожаловать в FastBox, {user.first_name}!\n"
        "Для завершения регистрации, пожалуйста, поделитесь своим номером телефона.",
        reply_markup=reply_markup
    )
    return PHONE

async def contact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    contact = update.message.contact
    
    phone_number = contact.phone_number if contact else None
    
    if phone_number:
        await db.add_user(user.id, user.username, user.full_name, phone_number)
        
        main_keyboard = [
            ["Создать заказ", "Мои заказы"],
            ["Поддержка"]
        ]
        reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "Регистрация успешна! Выберите действие в меню.",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, используйте кнопку, чтобы отправить номер телефона.")
        return PHONE

start_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        PHONE: [MessageHandler(filters.CONTACT, contact_callback)]
    },
    fallbacks=[],
)
