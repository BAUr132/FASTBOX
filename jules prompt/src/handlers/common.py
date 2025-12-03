from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from src.database import Database

db = Database()

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    orders = await db.get_orders(user.id)
    
    if not orders:
        await update.message.reply_text("У вас пока нет активных заказов.")
        return
    
    response = "Ваши заказы:\n\n"
    for order in orders:
        response += (
            f"Заказ #{order['id']}\n"
            f"Тип: {order['type']}\n"
            f"Статус: {order['status']}\n"
            f"Откуда: {order['sender_address']}\n"
            f"Куда: {order['receiver_address']}\n"
            f"------------------\n"
        )
    
    await update.message.reply_text(response)

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Связь с оператором: @support_fastbox\n"
        "Или позвоните по номеру: +7 777 123 45 67"
    )

my_orders_handler = MessageHandler(filters.Regex("^Мои заказы$"), my_orders)
support_handler = MessageHandler(filters.Regex("^Поддержка$"), support)
