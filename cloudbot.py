import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, JobQueue
)
from telegramalert import send_pattern_alerts, send_news_and_events
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if not TELEGRAM_TOKEN or TELEGRAM_CHAT_ID == 0:
    raise ValueError("❌ TELEGRAM_TOKEN or TELEGRAM_CHAT_ID must be set correctly in .env")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Command: /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🤖 Bot is running.")
    except Exception as e:
        logger.exception("Error in /start")
        await update.message.reply_text(f"❌ Error: {e}")

# --- Command: /scan ---
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbols = ["EURUSD", "XAUUSD", "US30"]
        await update.message.reply_text("🔍 Running full scan...")
        for symbol in symbols:
            await send_pattern_alerts(symbol)
            await send_news_and_events(symbol)
    except Exception as e:
        logger.exception("Error in /scan")
        await update.message.reply_text(f"❌ Error: {e}")

# --- Command: /status ---
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("✅ Status: Alive and monitoring.")
    except Exception as e:
        logger.exception("Error in /status")
        await update.message.reply_text(f"❌ Error: {e}")

# --- Background Job (15 min interval) ---
async def scheduled_job(context: ContextTypes.DEFAULT_TYPE):
    symbols = ["EURUSD", "XAUUSD", "US30"]
    for symbol in symbols:
        try:
            await send_pattern_alerts(symbol)
            await send_news_and_events(symbol)
        except Exception as e:
            logger.exception(f"❌ Background job failed for {symbol}: {e}")

# --- Main App ---
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("status", status))

    app.job_queue.run_repeating(scheduled_job, interval=900, first=10)

    await app.run_polling()

# --- Entrypoint ---
if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except Exception as e:
        logger.exception("❌ Fatal error in main bot loop")
