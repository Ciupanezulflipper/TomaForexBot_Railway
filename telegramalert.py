# telegramalert.py (cleaned + updated for proper pattern & news alerts)

import os
import logging
from dotenv import load_dotenv

from patterns import detect_patterns, PatternDetector
from marketdata import get_ohlc
from telegramsender import send_telegram_message
from finnhub_news_fetcher import fetch_recent_forex_news

load_dotenv()
logger = logging.getLogger(__name__)

TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

async def send_pattern_alerts(symbol: str, timeframe: str = 'H1'):
    try:
        ohlc = await get_ohlc(symbol, timeframe)
        df_with_patterns = detect_patterns(ohlc)

        if df_with_patterns.empty or 'Pattern' not in df_with_patterns.columns:
            logger.warning(f"[Pattern Alert] No usable pattern data for {symbol} ({timeframe})")
            return

        recent_patterns = PatternDetector.get_recent_patterns(df_with_patterns)

        if not recent_patterns:
            print(f"No patterns detected for {symbol} [{timeframe}].")
            return

        msg_lines = [f"📌 Pattern Alert for {symbol} [{timeframe}]\n"]
        for p in recent_patterns:
            direction = "🟢" if p.bullish else "🔴"
            msg_lines.append(f"{direction} {p.name} ({p.strength}) @ {p.timestamp.strftime('%H:%M')}")

        message = "\n".join(msg_lines)
        await send_telegram_message(message, TELEGRAM_CHAT_ID)

    except Exception as e:
        logger.error(f"Error in send_pattern_alerts for {symbol}: {e}")

async def send_news_and_events(symbol: str):
    try:
        news_items = await fetch_recent_forex_news()

        if not news_items:
            await send_telegram_message(f"📰 No fresh news for {symbol} yet.", TELEGRAM_CHAT_ID)
            return

        msg_lines = [f"📰 News Alert for {symbol}:\n"]
        for article in news_items:
            headline = article.get("headline", "No headline")
            url = article.get("url", "")
            msg_lines.append(f"- {headline}\n🔗 {url}\n")

        message = "\n".join(msg_lines)
        await send_telegram_message(message, TELEGRAM_CHAT_ID)

    except Exception as e:
        logger.error(f"Error in send_news_and_events for {symbol}: {e}")
