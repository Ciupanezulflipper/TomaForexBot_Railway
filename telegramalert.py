import os
import logging
from dotenv import load_dotenv

from patterns import detect_patterns, PatternDetector
from marketdata import get_ohlc
from telegramsender import send_telegram_message
from finnhub_news_fetcher import fetch_recent_forex_news
from news_memory import NewsMemory

# Load environment
load_dotenv()
logger = logging.getLogger(__name__)

# Validate chat ID
try:
    TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
    if TELEGRAM_CHAT_ID == 0:
        raise ValueError("❌ TELEGRAM_CHAT_ID is not set correctly in environment.")
except Exception as e:
    raise RuntimeError(f"Invalid TELEGRAM_CHAT_ID: {e}")

# Use separate memory files for clarity
PATTERN_MEMORY_FILE = "pattern_alert_memory.json"
NEWS_MEMORY_FILE = "news_alert_memory.json"


async def send_pattern_alerts(symbol: str, timeframe: str = 'H1'):
    memory = NewsMemory(PATTERN_MEMORY_FILE)
    try:
        ohlc = await get_ohlc(symbol, timeframe)
        df_with_patterns = detect_patterns(ohlc)

        if df_with_patterns.empty or 'Pattern' not in df_with_patterns.columns:
            logger.warning(f"[Pattern Alert] No pattern data for {symbol} [{timeframe}]")
            return

        recent_patterns = PatternDetector.get_recent_patterns(df_with_patterns)
        if not recent_patterns:
            logger.info(f"No patterns detected for {symbol} [{timeframe}]")
            return

        for p in recent_patterns:
            pattern_key = f"{symbol}:{timeframe}:{p.name}:{p.timestamp.isoformat()}"
            if memory.already_sent(pattern_key):
                continue

            direction = "🟢" if p.bullish else "🔴"
            message = (
                f"📌 <b>Pattern Alert</b> for <b>{symbol}</b> [{timeframe}]\n"
                f"{direction} <b>{p.name}</b> ({p.strength}) @ {p.timestamp.strftime('%H:%M')}"
            )
            await send_telegram_message(message, TELEGRAM_CHAT_ID, parse_mode="HTML")
            memory.remember_news(pattern_key)
            logger.info(f"[Pattern Alert] Sent: {pattern_key}")

    except Exception as e:
        logger.exception(f"❌ Error in send_pattern_alerts for {symbol}: {e}")


async def send_news_and_events(symbol: str):
    memory = NewsMemory(NEWS_MEMORY_FILE)
    try:
        news_items = await fetch_recent_forex_news()

        if not news_items:
            logger.info(f"[News] No news returned for {symbol}")
            return

        new_articles = [a for a in news_items if not memory.already_sent(a.get("url", ""))]
        if not new_articles:
            logger.info(f"[News] No new articles to alert for {symbol}")
            return

        msg_lines = [f"📰 <b>News Alert</b> for <b>{symbol}</b>:\n"]
        for article in new_articles:
            headline = article.get("headline", "No headline")
            url = article.get("url", "")
            msg_lines.append(f"🔸 {headline}\n<a href='{url}'>Read more</a>\n")
            memory.remember_news(url)

        message = "\n".join(msg_lines)
        await send_telegram_message(message, TELEGRAM_CHAT_ID, parse_mode="HTML")
        logger.info(f"[News Alert] Sent {len(new_articles)} articles for {symbol}")

    except Exception as e:
        logger.exception(f"❌ Error in send_news_and_events for {symbol}: {e}")
