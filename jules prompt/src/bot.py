import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler
from src.handlers.start import start_handler
from src.handlers.order import order_handler
from src.handlers.common import my_orders_handler, support_handler
from src.handlers.admin import admin_orders_handler, assign_courier_handler
from src.handlers.courier import courier_start_handler, my_deliveries_handler, set_status_handler
from src.database import Database

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    db = Database()
    await db.init()
    logger.info("Database initialized.")

def main():
    # Read token from environment variable
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN environment variable not set")
        return

    application = Application.builder().token(token).post_init(post_init).build()

    # User handlers
    application.add_handler(start_handler)
    application.add_handler(order_handler)
    application.add_handler(my_orders_handler)
    application.add_handler(support_handler)
    
    # Admin handlers
    application.add_handler(admin_orders_handler)
    application.add_handler(assign_courier_handler)
    
    # Courier handlers
    application.add_handler(courier_start_handler)
    application.add_handler(my_deliveries_handler)
    application.add_handler(set_status_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
