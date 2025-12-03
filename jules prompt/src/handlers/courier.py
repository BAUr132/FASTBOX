from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from src.database import Database

db = Database()

async def courier_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.add_user(user.id, user.username, user.full_name, is_courier=True)
    await update.message.reply_text(
        f"Вы зарегистрированы как курьер (ID: {user.id})!\n"
        "Сообщите этот ID администратору для назначения заказов.\n"
        "Ожидайте назначения заказов."
    )

async def my_deliveries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    orders = await db.get_courier_orders(user.id)
    
    if not orders:
        await update.message.reply_text("У вас нет назначенных заказов.")
        return
        
    response = "Ваши доставки:\n\n"
    for order in orders:
        response += (
            f"Заказ #{order['id']}\n"
            f"Статус: {order['status']}\n"
            f"Адрес отправителя: {order['sender_address']}\n"
            f"Адрес получателя: {order['receiver_address']}\n"
            f"Контакты получателя: {order['receiver_phone']}\n"
            f"------------------\n"
        )
    await update.message.reply_text(response)

async def set_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Usage: /set_status <order_id> <status>
    # Statuses: accepted, picked_up, delivered
    try:
        args = context.args
        if len(args) < 2:
             await update.message.reply_text("Использование: /set_status <ID заказа> <статус>\nСтатусы: accepted, picked_up, delivered")
             return
        
        order_id = int(args[0])
        status = args[1]
        
        allowed_statuses = ["accepted", "picked_up", "delivered"]
        if status not in allowed_statuses:
             await update.message.reply_text(f"Неверный статус. Доступные: {', '.join(allowed_statuses)}")
             return
             
        # Verify courier owns the order
        order = await db.get_order(order_id)
        if not order:
            await update.message.reply_text("Заказ не найден.")
            return
            
        if order['courier_id'] != update.effective_user.id:
            await update.message.reply_text("Вы не назначены на этот заказ.")
            return

        await db.update_order_status(order_id, status)
        await update.message.reply_text(f"Статус заказа #{order_id} изменен на '{status}'.")
        
        # Notify user
        try:
            status_messages = {
                "accepted": "Курьер принял ваш заказ.",
                "picked_up": "Курьер забрал вашу посылку.",
                "delivered": "Ваша посылка доставлена! Спасибо за использование FastBox."
            }
            msg_text = status_messages.get(status, f"Статус вашего заказа обновлен: {status}")
            
            await context.bot.send_message(chat_id=order['user_id'], text=f"📦 Заказ #{order_id}: {msg_text}")
        except Exception as e:
            await update.message.reply_text(f"Статус обновлен, но не удалось уведомить клиента: {e}")

    except ValueError:
        await update.message.reply_text("ID заказа должен быть числом.")

courier_start_handler = CommandHandler("courier_start", courier_start)
my_deliveries_handler = CommandHandler("my_deliveries", my_deliveries)
set_status_handler = CommandHandler("set_status", set_status)
