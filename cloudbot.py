# ─── cloudbot.py (cleaned + updated for python-telegram-bot v20+) ───
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
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ─── Logging ───
logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Telegram Commands ───
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is running! Use /calendar to check events.")

async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 Economic calendar feature is under construction.")

# ─── BotRunner Class ───
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
        await self.app.initialize()
        await self.app.start()
        await self.app.run_polling()

    async def stop(self):
        logger.info("🛑 Graceful shutdown started...")
        self.shutdown_event.set()
        if self.background_task:
            await self.background_task
        if self.app:
            await self.app.stop()
        logger.info("✅ Bot stopped.")

# ─── Signals ───
def setup_signal_handlers(runner: BotRunner):
    def stop_loop(signum, frame):
        logger.info(f"📴 Received signal {signum}.")
        asyncio.create_task(runner.stop())

    signal.signal(signal.SIGINT, stop_loop)
    signal.signal(signal.SIGTERM, stop_loop)

# ─── Main Entrypoint ───
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
    asyncio.run(asyncio.gather(main(), monitor_major_events()))


# ─── patterns.py (clean + only essential logic) ───
import pandas as pd
import logging
from typing import List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PatternResult:
    name: str
    strength: str
    bullish: bool
    timestamp: pd.Timestamp

class PatternDetector:
    @classmethod
    def detect_patterns(cls, df: pd.DataFrame) -> pd.DataFrame:
        result_df = df.copy()
        result_df['Pattern'] = ''
        result_df['Pattern_Strength'] = ''

        # Normalize column names
        rename_map = {
            'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'
        }
        result_df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

        if not all(col in result_df.columns for col in ['Open', 'High', 'Low', 'Close']):
            logger.error("Missing OHLC columns.")
            return result_df

        open_ = result_df['Open'].values
        close = result_df['Close'].values

        for i in range(1, len(result_df)):
            if close[i] > open_[i] and close[i-1] < open_[i-1] and close[i] > open_[i-1] and open_[i] < close[i-1]:
                result_df.at[result_df.index[i], 'Pattern'] = "🟢 Bullish Engulfing"
                result_df.at[result_df.index[i], 'Pattern_Strength'] = "Strong"
            elif close[i] < open_[i] and close[i-1] > open_[i-1] and open_[i] > close[i-1] and close[i] < open_[i-1]:
                result_df.at[result_df.index[i], 'Pattern'] = "🔴 Bearish Engulfing"
                result_df.at[result_df.index[i], 'Pattern_Strength'] = "Strong"

        return result_df

    @classmethod
    def get_recent_patterns(cls, df: pd.DataFrame, lookback: int = 3) -> List[PatternResult]:
        if 'Pattern' not in df.columns:
            return []

        recent_df = df.tail(lookback)
        patterns = []
        for idx, row in recent_df.iterrows():
            if isinstance(row['Pattern'], str) and row['Pattern']:
                patterns.append(PatternResult(
                    name=row['Pattern'].replace("🟢 Bullish ", "").replace("🔴 Bearish ", ""),
                    strength=row['Pattern_Strength'],
                    bullish="🟢" in row['Pattern'],
                    timestamp=idx if hasattr(idx, 'strftime') else pd.Timestamp.now()
                ))
        return patterns

def detect_candle_patterns(df: pd.DataFrame) -> pd.DataFrame:
    return PatternDetector.detect_patterns(df)

detect_patterns = PatternDetector.detect_patterns
