from dotenv import load_dotenv
load_dotenv()  # ✅ Load before anything else

import os
import asyncio
import logging
import signal
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

from eventdriven_scheduler import monitor_major_events
from telegramalert import send_pattern_alerts, send_news_and_events

# ─── Logging Setup ───
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# ─── Command Handlers ───
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 TomaForexBot is running. Use /scan or /status.")

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbols = ["EURUSD", "XAUUSD", "US30"]
    await update.message.reply_text("🔍 Running full scan on EURUSD, XAUUSD, US30...")
    for symbol in symbols:
        await send_pattern_alerts(symbol)
        await send_news_and_events(symbol)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is online and scheduler is active.")

# ─── Combined Runner Class ───
class BotRunner:
    def __init__(self):
        self.app = None
        self.shutdown_event = asyncio.Event()

    async def background_tasks(self):
        while not self.shutdown_event.is_set():
            try:
                symbols = ["EURUSD", "XAUUSD", "US30"]
                for symbol in symbols:
                    await send_pattern_alerts(symbol)
                    await send_news_and_events(symbol)
                logger.info("✅ Background alerts done.")
                await asyncio.wait_for(self.shutdown_event.wait(), timeout=900)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[Background] {e}")

    async def start(self):
        self.app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        self.app.add_handler(CommandHandler("start", start))
        self.app.add_handler(CommandHandler("scan", scan))
        self.app.add_handler(CommandHandler("status", status))

        await self.app.initialize()
        await self.app.start()
        await self.app.bot.set_my_commands([
            ("start", "Start the bot"),
            ("scan", "Scan major symbols"),
            ("status", "Bot status"),
        ])

        asyncio.create_task(self.background_tasks())
        asyncio.create_task(monitor_major_events())

        logger.info("🤖 Starting Telegram bot polling...")
        await self.app.run_polling()

    async def stop(self):
        self.shutdown_event.set()
        if self.app:
            await self.app.stop()
            await self.app.shutdown()
        logger.info("🛑 Bot shutdown complete.")

def setup_signals(runner: BotRunner):
    def handler(signum, frame):
        logger.info(f"📴 Signal received: {signum}")
        asyncio.create_task(runner.stop())

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

# ─── Entrypoint ───
async def main():
    runner = BotRunner()
    setup_signals(runner)
    try:
        await runner.start()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        await runner.stop()

if __name__ == "__main__":
    asyncio.run(main())
