# TomaForexBot/telegrambot.py

import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# Initialize the Telegram application
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# ✅ /start handler
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🚨 /start received from {update.effective_user.id}")
    await update.message.reply_text("👋 Hello from Railway. Bot is live.")

# ✅ /gold handler (basic test)
async def handle_gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 /gold received from {update.effective_user.id}")
    await update.message.reply_text("✅ Gold handler works!")

# ✅ Start polling
async def start_telegram_listener():
    print("🚀 Minimal bot is running...")
    telegram_app.add_handler(CommandHandler("start", handle_start))
    telegram_app.add_handler(CommandHandler("gold", handle_gold))
    print("✅ Handlers ready.")
    await telegram_app.run_polling(stop_signals=None)
