import os
import asyncio
import signal
import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram.error import TelegramError

from telegrambot import start_command, calendar_command
from pattern_alerts import send_pattern_alerts
from news_alerts import send_news_and_events

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                logger.info("✅ Alerts sent")
            except Exception as e:
                logger.error(f"[Background Loop] {e}")
            try:
                await asyncio.wait_for(self.shutdown_event.wait(), timeout=60 * 15)
            except asyncio.TimeoutError:
                continue

    async def start(self):
        self.app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        self.app.add_handler(CommandHandler("start", start_command))
        self.app.add_handler(CommandHandler("calendar", calendar_command))

        await self.app.initialize()
        await self.app.start()

        self.background_task = asyncio.create_task(self.background_alerts())

        try:
            await self.app.updater.start_polling()
            await self.app.updater.wait_for_stop()
        finally:
            await self.stop()

    async def stop(self):
        logger.info("🛑 Graceful shutdown started...")
        self.shutdown_event.set()
        if self.background_task:
            await self.background_task
        if self.app:
            await self.app.stop()
            await self.app.shutdown()

def setup_signal_handlers(runner: BotRunner):
    def _handler(sig, frame):
        logger.info(f"🔔 Signal received: {sig}")
        asyncio.create_task(runner.stop())

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)

async def main():
    runner = BotRunner()
    setup_signal_handlers(runner)
    await runner.start()

# ⚠️ DO NOT use asyncio.run() directly — check if loop exists
if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except Exception as e:
        logger.error(f"❌ Fatal: {e}")
