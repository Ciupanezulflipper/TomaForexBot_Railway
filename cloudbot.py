import os
import signal
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import pandas as pd
from typing import List

# ────────────── Load .env and config ──────────────
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# ────────────── Logging ──────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)

# ────────────── Imports ──────────────
from marketdata import get_ohlc
from indicators import calculate_rsi
from patterns import detect_candle_patterns, PatternResult
from economic_calendar_module import fetch_all_calendar, analyze_events

# ────────────── Telegram Commands ──────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is running and ready!")

async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        events = analyze_events(fetch_all_calendar())
        if not events:
            await update.message.reply_text("📅 No major economic events now.")
            return

        msg = "📅 Upcoming Economic Events:\n\n"
        for e in events[:5]:
            msg += f"{e['date']} - {e['event']} - {e['impact']}\n"

        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"[Calendar] {e}")
        await update.message.reply_text(f"❌ Error: {e}")

# ────────────── Alert System ──────────────
async def send_pattern_alerts():
    PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
    TIMEFRAME = "H1"
    for symbol in PAIRS:
        try:
            df = await get_ohlc(symbol, TIMEFRAME, bars=100)
            if df is None or df.empty:
                logger.warning(f"[{symbol}] No data.")
                continue

            patterns = detect_candle_patterns(df)
            rsi_series = calculate_rsi(df["close"], 14)
            latest_rsi = rsi_series.iloc[-1] if isinstance(rsi_series, pd.Series) else rsi_series

            alerts = []
            for p in patterns[-3:]:
                if "Bullish" in p and latest_rsi < 35:
                    alerts.append(f"🟢 BUY {symbol} ({TIMEFRAME})\n{p}\nRSI: {latest_rsi:.2f}")
                elif "Bearish" in p and latest_rsi > 65:
                    alerts.append(f"🔴 SELL {symbol} ({TIMEFRAME})\n{p}\nRSI: {latest_rsi:.2f}")

            for alert in alerts:
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=alert)

        except Exception as e:
            logger.error(f"[Alert Error] {symbol}: {e}")

# ────────────── Bot Runner ──────────────
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
                logger.info("✅ Alerts sent.")
            except Exception as e:
                logger.error(f"[Alert Loop Error] {e}")

            try:
                await asyncio.wait_for(self.shutdown_event.wait(), timeout=900)
            except asyncio.TimeoutError:
                continue

    async def start(self):
        self.app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        self.app.add_handler(CommandHandler("start", start_command))
        self.app.add_handler(CommandHandler("calendar", calendar_command))

        self.background_task = asyncio.create_task(self.background_alerts())
        await self.app.run_polling()

    async def stop(self):
        logger.info("🛑 Graceful shutdown started...")
        self.shutdown_event.set()

        if self.background_task:
            await self.background_task

        if self.app:
            await self.app.shutdown()
            await self.app.stop()

# ────────────── Signal Handlers ──────────────
def setup_signal_handlers(runner: BotRunner):
    def _signal_handler(sig, frame):
        logger.info(f"🚨 Received signal: {sig}")
        asyncio.create_task(runner.stop())

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

# ────────────── Entrypoint ──────────────
async def main():
    runner = BotRunner()
    setup_signal_handlers(runner)

    try:
        await runner.start()
    except KeyboardInterrupt:
        logger.info("🔌 Stopped by keyboard")
    except Exception as e:
        logger.error(f"❌ Fatal: {e}")
    finally:
        await runner.stop()

if __name__ == "__main__":
    asyncio.run(main())
