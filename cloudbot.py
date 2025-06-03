# cloudbot.py
import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Bot
import pandas as pd

from botstrategies import analyze_symbol_single
from patterns import detect_candle_patterns
from indicators import calculate_rsi
from news_feeds import analyze_all_feeds
from economic_calendar_module import fetch_all_calendar, analyze_events

# ---- ENV/SETUP ----
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)

# ---- MAIN LOGIC ----

async def send_pattern_alerts():
    from marketdata import get_mt5_data

    PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
    TIMEFRAME = "H1"
    MIN_RSI_BUY = 35
    MAX_RSI_SELL = 65

    for symbol in PAIRS:
        df = get_mt5_data(symbol, TIMEFRAME, bars=100)
        if df is None or df.empty:
            logger.warning(f"[{symbol}] No data.")
            continue
        df = detect_candle_patterns(df)
        rsi = calculate_rsi(df["close"], 14)
        df["RSI"] = rsi

        last = df.iloc[-1]
        last_pattern = last.get("Pattern", "")
        last_rsi = last.get("RSI", None)
        last_close = last.get("close", None)

        alert = None
        # Bullish patterns + low RSI = Buy alert
        if any(p in last_pattern for p in ["Bullish Engulfing", "Hammer", "Morning Star"]):
            if last_rsi is not None and last_rsi < MIN_RSI_BUY:
                alert = f"BUY Signal on {symbol} ({TIMEFRAME})\nPattern: {last_pattern}\nRSI: {last_rsi:.2f}\nClose: {last_close}"
        # Bearish patterns + high RSI = Sell alert
        if any(p in last_pattern for p in ["Bearish Engulfing", "Shooting Star", "Evening Star"]):
            if last_rsi is not None and last_rsi > MAX_RSI_SELL:
                alert = f"SELL Signal on {symbol} ({TIMEFRAME})\nPattern: {last_pattern}\nRSI: {last_rsi:.2f}\nClose: {last_close}"

        if alert:
            try:
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=alert)
                logger.info(f"[ALERT SENT] {alert}")
            except Exception as e:
                logger.error(f"Failed to send Telegram alert: {e}")

async def send_news_and_events():
    # News signals
    logic_alerts, events = analyze_all_feeds()
    for a in logic_alerts[:10]:  # Limit to top 10
        msg = f"📰 {a['headline']} => {a['asset']} {a['signal']} (reason: {a['reason']})"
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        except Exception as e:
            logger.error(f"[NEWS ALERT ERROR] {e}")

    # Economic calendar
    major_events = analyze_events(fetch_all_calendar())
    for e in major_events[:5]:  # Only most urgent events
        msg = f"🗓 {e['date']} | {e['event']} | Impact: {e['impact']} | Affected: {e['affected']}"
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        except Exception as e:
            logger.error(f"[ECON EVENT ALERT ERROR] {e}")

async def bot_main_loop():
    logger.info("Bot main loop started.")
    while True:
        try:
            await send_pattern_alerts()
            await send_news_and_events()
        except Exception as e:
            logger.error(f"[MAIN LOOP ERROR] {e}")
        await asyncio.sleep(60 * 15)  # 15 minutes

if __name__ == "__main__":
    logger.info("Starting TomaForexBot cloudbot.py...")
    asyncio.run(bot_main_loop())
