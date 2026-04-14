import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    WebAppInfo, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    MenuButtonWebApp
)

# Берем данные из переменных окружения Railway
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise ValueError("Переменная BOT_TOKEN не установлена!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def set_main_menu_button(bot: Bot):
    """Устанавливает кнопку Mini App рядом с вложением (Menu Button)"""
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Открыть FastBox",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # 1. Кнопка под сообщением (Inline)
    inline_markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Запустить в чате", 
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]
    ])

    # 2. Кнопка вместо клавиатуры (Reply Keyboard) — то, что вы просили
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📦 Открыть FastBox", 
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ]
        ],
        resize_keyboard=True # Делает кнопку компактной
    )
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Добро пожаловать в FastBox.\n"
        f"Нажми на кнопку ниже или в меню, чтобы запустить приложение!",
        reply_markup=reply_markup # Устанавливаем основную клавиатуру
    )
    
    # Отправляем еще и инлайн кнопку для красоты
    await message.answer("Также вы можете использовать быструю ссылку:", reply_markup=inline_markup)

async def main():
    await set_main_menu_button(bot)
    logging.info(f"Бот запущен! Используется URL: {WEBAPP_URL}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот выключен")
