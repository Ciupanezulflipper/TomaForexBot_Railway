import os
import asyncio
import logging
import signal
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from eventdriven_scheduler import monitor_major_events
from telegramalert import send_pattern_alerts, send_news_and_events
from dotenv import load_dotenv

# ─── Load Environment ───
load_dotenv()

# ─── Logging Setup ───
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Global Constants ───
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ─── Telegram Handlers ───
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is running! Use /calendar to check events.")

async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 Economic calendar feature is under construction.")

# ─── Bot Lifecycle Class ───
class BotRunner:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.background_task = None
        self.app = None

    async def background_alerts(self):
        logger.info("🔁 Background alerts running...")
        symbols = ["EURUSD", "XAUUSD", "US30"]
        timeframes = ["H1"]

        while not self.shutdown_event.is_set():
            try:
                for symbol in symbols:
                    for tf in timeframes:
                        await send_pattern_alerts(symbol, tf)
                        await send_news_and_events(symbol)
                logger.info("✅ Alerts sent.")
            except Exception as e:
                logger.error(f"[Background] {e}")
            try:
                await asyncio.wait_for(self.shutdown_event.wait(), timeout=900)
            except asyncio.TimeoutError:
                continue

    async def start(self):
        self.app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        self.app.add_handler(CommandHandler("start", start_command))
        self.app.add_handler(CommandHandler("calendar", calendar_command))

        self.background_task = asyncio.create_task(self.background_alerts())

        try:
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            await self.app.updater.idle()
        finally:
            await self.stop()

    async def stop(self):
        logger.info("🛑 Graceful shutdown started...")
        self.shutdown_event.set()
        if self.background_task:
            await self.background_task
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
        logger.info("✅ Bot stopped.")

# ─── Signal Setup ───
def setup_signal_handlers(runner: BotRunner):
    def stop_loop(signum, frame):
        logger.info(f"📴 Received signal {signum}.")
        asyncio.create_task(runner.stop())

    signal.signal(signal.SIGINT, stop_loop)
    signal.signal(signal.SIGTERM, stop_loop)

# ─── Entrypoint for CLI ───
async def main():
    logger.info("🚀 Launching bot...")
    runner = BotRunner()
    setup_signal_handlers(runner)
    try:
        await runner.start()
    except Exception as e:
        logger.error(f"❌ Fatal: {e}")
    finally:
        await runner.stop()

# ─── Entrypoint for Web ───
async def run_bot_loop():
    await asyncio.gather(main(), monitor_major_events())

# ─── Main Block ───
if __name__ == "__main__":
    asyncio.run(run_bot_loop())
