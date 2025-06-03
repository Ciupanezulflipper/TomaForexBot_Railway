import os
from dotenv import load_dotenv
from telegram import Bot, InputFile

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def send_telegram_message(message, chat_id):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=chat_id, text=message)

async def send_telegram_photo(image_path, chat_id):
    bot = Bot(token=TELEGRAM_TOKEN)
    with open(image_path, "rb") as img:
        await bot.send_photo(chat_id=chat_id, photo=InputFile(img))
