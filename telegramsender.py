# telegramsender.py

import os
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN not found in .env file!")

# Send a plain text message (async)
async def send_telegram_message(message, chat_id):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')

# Send an image/photo (async)
async def send_telegram_photo(chat_id, photo_path, caption=None):
    bot = Bot(token=TELEGRAM_TOKEN)
    with open(photo_path, 'rb') as photo:
        await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)
