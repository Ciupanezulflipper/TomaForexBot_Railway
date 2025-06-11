# core/utils.py

import os
import logging
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

bot = Bot(token=TELEGRAM_TOKEN)
logger = logging.getLogger(__name__)

def send_telegram_message(message):
    """Send a plain text message via Telegram bot."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials missing.")
        return

    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='Markdown')
        logger.info(f"[TELEGRAM] Sent: {message[:50]}...")
    except Exception as e:
        logger.error(f"[TELEGRAM ERROR] {e}")
