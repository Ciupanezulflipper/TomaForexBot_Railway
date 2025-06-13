import aiohttp
import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update, Bot
import pandas as pd
from typing import List

# Import your existing modules
from botstrategies import analyze_symbol_single
from core.signal_fusion import generate_trade_decision
from charting import generate_pro_chart_async
from marketdata import get_ohlc
from economic_calendar_module import fetch_major_events, fetch_all_calendar, analyze_events
from statushandler import handle_status, connect_finnhub, connect_yahoo
from news_fetcher import fetch_combined_news
from news_signal_logic import analyze_multiple_headlines
from news_feeds import analyze_all_feeds
from patterns import detect_candle_patterns
from patterns import detect_candle_patterns, PatternDetector, PatternResult
from indicators import calculate_rsi

# Load environment
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global bot instance
bot = Bot(token=TELEGRAM_TOKEN)


# ────────────── Command: /calendar ──────────────
async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        events = analyze_events(fetch_all_calendar())
        if not events:
            await update.message.reply_text("📅 No major economic events right now.")
            return

        msg = "📅 Upcoming Economic Events:\n\n"
        for e in events[:6]:
            msg += f"{e['date']} - {e['event']} - {e['impact']}\n"

        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"[Calendar] {e}")
        await update.message.reply_text(f"❌ Error: {e}")


# ────────────── Pattern Alerts ──────────────
async def send_pattern_alerts():
    PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
    TIMEFRAME = "H1"
    MIN_RSI_BUY = 35
    MAX_RSI_SELL = 65

    for symbol in PAIRS:
        try:
            df = await get_ohlc(symbol, TIMEFRAME, bars=100)
            if df is None or df.empty:
                logger.warning(f"[{symbol}] No data.")
                continue

            patterns = detect_candle_patterns(df, max_patterns=3)
            rsi_series = calculate_rsi(df["close"], 14)
            latest_rsi = rsi_series.iloc[-1] if isinstance(rsi_series, pd.Series) else rsi_series

            alert = None

            if any(p for p in patterns if "Bullish" in p):
                if latest_rsi < MIN_RSI_BUY:
                    alert = f"🚀 BUY Signal on {symbol} ({TIMEFRAME})\nPattern: {patterns[-1]}\nRSI: {latest_rsi:.2f}"

            elif any(p for p in patterns if "Bearish" in p):
                if latest_rsi > MAX_RSI_SELL:
                    alert = f"📉 SELL Signal on {symbol} ({TIMEFRAME})\nPattern: {patterns[-1]}\nRSI: {latest_rsi:.2f}"

            if alert:
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=alert)

        except Exception as exc:
            logger.error(f"[Pattern Alert] {symbol}: {exc}")


async def send_pair_pattern_alert(pair: str, patterns: List[PatternResult], df: pd.DataFrame):
    """Send a formatted alert message for a single trading pair."""
    try:
        current_price = df["close"].iloc[-1]
        price_change = ((df["close"].iloc[-1] / df["close"].iloc[-2]) - 1) * 100

        pattern_texts = []
        for pattern in patterns:
            direction_emoji = "🟢" if pattern.bullish else "🔴"
            direction_text = "Bullish" if pattern.bullish else "Bearish"
            strength_emoji = get_strength_emoji(pattern.strength)
            pattern_texts.append(f"{direction_emoji} {direction_text} {pattern.name} {strength_emoji}")

        alert_message = f"""
🔍 **Pattern Alert: {pair}**

📊 **Current Price:** {current_price:.5f}
📈 **Change:** {price_change:+.2f}%

🕯️ **Detected Patterns:**
{chr(10).join(f"• {p}" for p in pattern_texts)}

⏰ **Time:** {pd.Timestamp.now().strftime('%H:%M:%S UTC')}

#PatternAlert #{pair} #TechnicalAnalysis
""".strip()

        await send_to_all_channels(alert_message)
        logger.info(f"📊 Pattern alert sent for {pair}: {len(patterns)} patterns detected")

    except Exception as exc:
        logger.error(f"Error sending pattern alert for {pair}: {exc}")


def get_strength_emoji(strength: str) -> str:
    """Return an emoji representing the given strength label."""
    strength_lower = strength.lower()
    if strength_lower == "strong":
        return "🔥"
    if strength_lower == "medium":
        return "⚡"
    if strength_lower == "weak":
        return "💫"
    return "📊"


async def send_to_all_channels(message: str):
    """Send a message to all configured notification channels."""
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as exc:
        logger.error(f"Error sending to channels: {exc}")


# ────────────── News + Calendar Alerts ──────────────
async def send_news_and_events():
    try:
        news = await fetch_combined_news()
        if news:
            headlines = [f"📰 {item['headline']}" for item in news[:3]]
            msg = "🗞 Top News:\n" + "\n".join(headlines)
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

        events = analyze_events(fetch_all_calendar())
        for event in events[:3]:
            msg = f"🗓 {event['date']} | {event['event']}\nImpact: {event['impact']} | Affected: {event['affected']}"
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except Exception as e:
        logger.error(f"[News/Events] {e}")


# ────────────── Background Alert Loop ──────────────
# ────────────── Background Alert Loop ──────────────
async def background_alerts():
    logger.info("Background alert system started")
    while True:
        try:
            await send_pattern_alerts()
            await send_news_and_events()
            logger.info("✅ Alerts sent")
        except Exception as e:
            logger.error(f"[Background Loop] {e}")
        await asyncio.sleep(60 * 15)  # 15 minutes