from dotenv import load_dotenv
load_dotenv()  # ✅ Load before anything else

import os
import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from eventdriven_scheduler import monitor_major_events
from telegramalert import send_pattern_alerts, send_news_and_events

# ─── Logging Setup ───
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Load Telegram Token ───
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# ─── Telegram Command Handlers ───
async def start(update, context):
    await update.message.reply_text("👋 TomaForexBot is running. Use /scan or /status.")

async def scan(update, context):
    symbols = ["EURUSD", "XAUUSD", "US30"]
    await update.message.reply_text("🔍 Running full scan on EURUSD, XAUUSD, US30...")
    for symbol in symbols:
        await send_pattern_alerts(symbol)
        await send_news_and_events(symbol)

async def status(update, context):
    await update.message.reply_text("✅ Bot is online and scheduler is active.")

# ─── Telegram App Setup ───
async def main():
    logger.info("🚀 Launching bot...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("status", status))

    await app.bot.set_my_commands([
        ("start", "Start the bot"),
        ("scan", "Scan symbols"),
        ("status", "Bot status")
    ])

    logger.info("🤖 Starting Telegram bot polling...")
    await app.run_polling(close_loop=False)

# ─── Entry Point: Run Bot + Scheduler ───
async def run_all():
    await asyncio.gather(
        main(),
        monitor_major_events()
    )

if __name__ == "__main__":
    try:
        asyncio.run(run_all())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Gracefully shutting down...")
