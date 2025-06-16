import os
from eventdriven_scheduler import monitor_major_events
import asyncio
import logging
import signal
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from telegramalert import send_pattern_alerts, send_news_and_events
from dotenv import load_dotenv

load_dotenv()

# ───── Logging ─────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ───── ENV ─────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ───── Handlers ─────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is running! Use /calendar to check events.")

async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 Economic calendar feature is under construction.")

# ───── Bot Runner ─────
class BotRunner:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.background_task = None
        self.app = None

    async def background_alerts(self):
        logger.info("🔁 Background alerts running...")
        while not self.shutdown_event.is_set():
            try:
                await send_pattern_alerts()
                await send_news_and_events()
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
            await self.app.run_polling()
        finally:
            await self.stop()

    async def stop(self):
        logger.info("🛑 Graceful shutdown started...")
        self.shutdown_event.set()
        if self.background_task:
            await self.background_task
        if self.app:
            logger.info("✅ Bot stopped.")

# ───── Signal Handling ─────
def setup_signal_handlers(runner: BotRunner):
    def stop_loop(signum, frame):
        logger.info(f"📴 Received signal {signum}.")
        asyncio.create_task(runner.stop())

    signal.signal(signal.SIGINT, stop_loop)
    signal.signal(signal.SIGTERM, stop_loop)

# ───── Entrypoint ─────
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

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(monitor_major_events())
    loop.run_forever()
