# PATCHED test_bot_minimal.py (removed hardcoded token)
import os
from telegram import Bot

# Use environment variable
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if TELEGRAM_TOKEN:
    bot = Bot(token=TELEGRAM_TOKEN)
    print("✅ Bot instance created")
else:
    print("⚠️ TELEGRAM_TOKEN not found")