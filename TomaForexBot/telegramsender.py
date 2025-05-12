import os
from dotenv import load_dotenv
from telegram import Bot, InputFile

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

bot = Bot(token=TELEGRAM_TOKEN)

async def send_telegram_message(message):
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

async def send_telegram_photo(image_path):
    with open(image_path, "rb") as img:
        await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=InputFile(img))
