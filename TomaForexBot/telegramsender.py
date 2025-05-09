# telegramsender.py

import os
from dotenv import load_dotenv
from telegram import InputFile
from telegram.ext import ApplicationBuilder

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# ✅ Text message
async def send_telegram_message(message: str, chat_id: int = TELEGRAM_CHAT_ID):
    if telegram_app and chat_id:
        await telegram_app.bot.send_message(chat_id=chat_id, text=message)

# ✅ Photo message
async def send_telegram_photo(image_path: str, chat_id: int = TELEGRAM_CHAT_ID):
    if telegram_app and chat_id and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            await telegram_app.bot.send_photo(chat_id=chat_id, photo=InputFile(f))
