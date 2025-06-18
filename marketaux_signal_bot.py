import os
import re
import aiohttp
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError
import yfinance as yf
import logging
import csv
from news_memory import NewsMemory

# Load environment variables
load_dotenv()

MARKETAUX_API_KEY = os.getenv("MARKETAUX_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not MARKETAUX_API_KEY or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise RuntimeError("API keys and chat ID must be set in environment variables.")

TELEGRAM_CHAT_ID = int(TELEGRAM_CHAT_ID)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

ASSETS = {
    "USDJPY": ["USDJPY", "yen", "japanese yen"],
    "US30": ["US30", "Dow", "Dow Jones"],
    "USDCHF": ["USDCHF", "swiss franc", "franc"],
    "OIL": ["OIL", "Brent", "WTI", "crude"]
}

KEYWORDS_BULLISH = [
    "attack", "conflict", "tension", "strike", "hawkish", "rate cut", "stimulus", "buy", "surge", "rally"
]
KEYWORDS_BEARISH = [
    "rate hike", "dovish", "recession", "sell", "drop", "fall", "plunge", "bearish", "resistance"
]

SIGNAL_LOG_FILE = "signals_log.csv"

async def fetch_news(symbol="US30"):
    try:
        url = "https://api.marketaux.com/v1/news/all"
        params = {
            "api_token": MARKETAUX_API_KEY,
            "symbols": symbol,
            "language": "en",
            "published_after": (datetime.utcnow() - timedelta(hours=2)).isoformat()
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=15) as response:
                data = await response.json()
                return data.get("data", [])
    except Exception as e:
        logger.error(f"[Marketaux] Error fetching news: {e}")
        return []

def extract_asset(text):
    text = text.lower()
    for asset, keywords in ASSETS.items():
        for kw in keywords:
            if kw.lower() in text:
                return asset
    return None

def keyword_sentiment(text, asset):
    text = text.lower()
    if any(kw in text for kw in KEYWORDS_BULLISH):
        return ("BUY", "Bullish") if asset == "OIL" else ("SELL", "Bearish")
    if any(kw in text for kw in KEYWORDS_BEARISH):
        return ("SELL", "Bearish") if asset in ["USDJPY", "USDCHF", "US30"] else ("BUY", "Bullish")
    return "HOLD", "Neutral"

def get_atr(symbol, period=7):
    try:
        df = yf.download(symbol, period=f"{period+2}d", interval="1d", progress=False)
        if df.empty:
            return None
        df['H-L'] = df['High'] - df['Low']
        df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
        df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        atr = df['TR'].rolling(window=period).mean().iloc[-1]
        return round(atr, 4)
    except Exception as e:
        logger.warning(f"[ATR] Failed to calculate ATR for {symbol}: {e}")
        return None

def format_telegram_message(asset, signal, explanation, sl, tp, news, timeframe="12H"):
    asset_hashtag = f"#{asset}"
    return (
        f"<b>{asset} What Next? {signal}!</b>\n\n"
        f"📝 <b>My dear followers,</b>\n"
        f"This is my opinion on the {asset} next move:\n"
        f"{explanation}\n"
        f"<b>Safe Stop Loss</b> – {sl}\n"
        f"<b>Goal</b> – {tp}\n"
        f"{asset_hashtag}\n"
        f"<b>Time Frame:</b> {timeframe} (signal)\n"
        f"\n"
        f"📰 <i>{news['title']}</i>\n"
        f"🔗 <a href='{news['url']}'>Read more</a>\n"
        f"\n"
        f"WISH YOU ALL LUCK 🍀🍀\n"
    )

def log_signal(signal_data, log_file=SIGNAL_LOG_FILE):
    fieldnames = [
        "asset", "signal", "bias", "entry", "sl", "tp",
        "timestamp", "news_url", "news_title"
    ]
    file_exists = os.path.isfile(log_file)
    with open(log_file, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(signal_data)

def send_telegram_message_sync(message):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='HTML',
            disable_web_page_preview=False
        )
        logger.info("[Telegram] Signal sent.")
    except TelegramError as e:
        logger.error(f"[Telegram] Failed to send message: {e}")

async def analyze_and_alert_asset(asset, memory: NewsMemory):
    news_items = await fetch_news(asset)
    for news in news_items:
        news_url = news.get('url')
        if not news_url or memory.already_sent(news_url):
            continue

        text = news['title'] + ". " + news.get('description', '')
        detected_asset = extract_asset(text)
        if not detected_asset:
            continue

        signal, bias = keyword_sentiment(text, detected_asset)
        if signal == "HOLD":
            continue

        atr = get_atr(detected_asset)
        if not atr:
            continue

        try:
            df = yf.download(detected_asset, period="2d", interval="1h", progress=False)
            entry = round(df['Close'][-1], 4) if not df.empty else 0
        except Exception as e:
            logger.warning(f"[YFinance] Failed to get entry for {detected_asset}: {e}")
            continue

        sl = round(entry + atr, 4) if signal == "BUY" else round(entry - atr, 4)
        tp = round(entry + 2 * atr, 4) if signal == "BUY" else round(entry - 2 * atr, 4)

        explanation = f"The asset is approaching an important pivot point {entry}\nBias – {bias}"

        message = format_telegram_message(detected_asset, signal, explanation, sl, tp, news)

        # Sync send to avoid python-telegram-bot async issues
        send_telegram_message_sync(message)

        # Log and remember
        memory.remember_news(news_url)
        signal_data = {
            "asset": detected_asset,
            "signal": signal,
            "bias": bias,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "timestamp": datetime.now().isoformat(),
            "news_url": news_url,
            "news_title": news['title'],
        }
        log_signal(signal_data)
        logger.info(f"[Signal] Logged {signal} signal for {detected_asset} at {entry}")

async def job_loop():
    memory = NewsMemory()
    while True:
        logger.info("Starting Marketaux signal check...")
        tasks = [analyze_and_alert_asset(asset, memory) for asset in ASSETS.keys()]
        await asyncio.gather(*tasks)
        logger.info("Sleeping for 15 minutes...")
        await asyncio.sleep(15 * 60)

if __name__ == "__main__":
    asyncio.run(job_loop())