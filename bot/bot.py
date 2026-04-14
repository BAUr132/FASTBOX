import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, MenuButtonWebApp

# Берем данные из переменных окружения Railway
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise ValueError("Переменная BOT_TOKEN не установлена!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def set_main_menu_button(bot: Bot):
    """Устанавливает кнопку Mini App рядом с клавиатурой"""
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Открыть FastBox",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Запустить приложение", 
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]
    ])
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Добро пожаловать в FastBox — сервис моментальной доставки.\n"
        f"Нажми на кнопку ниже, чтобы запустить приложение!",
        reply_markup=markup
    )

async def main():
    await set_main_menu_button(bot)
    logging.info(f"Бот запущен! Используется URL: {WEBAPP_URL}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот выключен")
