import os
from dotenv import load_dotenv
import requests
import re
import yfinance as yf
from datetime import datetime, timedelta
from telegram import Bot

# --- Load Env Vars ---
load_dotenv()
MARKETAUX_API_KEY = os.getenv("MARKETAUX_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# --- Asset and Keyword Setup ---
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

# --- 1. Fetch News ---
def fetch_news(symbol="US30"):
    url = "https://api.marketaux.com/v1/news/all"
    params = {
        "api_token": MARKETAUX_API_KEY,
        "symbols": symbol,
        "language": "en",
        "published_after": (datetime.utcnow() - timedelta(hours=2)).isoformat()
    }
    r = requests.get(url, params=params)
    return r.json().get("data", [])

# --- 2. Asset Extraction ---
def extract_asset(text):
    text = text.lower()
    for asset, keywords in ASSETS.items():
        for kw in keywords:
            if kw.lower() in text:
                return asset
    return None

# --- 3. Keyword Sentiment Analysis ---
def keyword_sentiment(text, asset):
    text = text.lower()
    if any(kw in text for kw in KEYWORDS_BULLISH):
        if asset == "OIL":
            return "BUY", "Bullish"
        else:
            return "SELL", "Bearish"
    if any(kw in text for kw in KEYWORDS_BEARISH):
        if asset in ["USDJPY", "USDCHF", "US30"]:
            return "SELL", "Bearish"
        else:
            return "BUY", "Bullish"
    return "HOLD", "Neutral"

# --- 4. ATR-based SL/TP Calculation ---
def get_atr(symbol, period=7):
    df = yf.download(symbol, period=f"{period+2}d", interval="1d")
    if df.empty:
        return None
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    atr = df['TR'].rolling(window=period).mean().iloc[-1]
    return round(atr, 4)

# --- 5. Signal Message Formatting ---
def format_telegram_message(asset, signal, explanation, sl, tp, news, timeframe="12H"):
    asset_hashtag = f"#{asset}"
    msg = (
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
    return msg

# --- 6. Send to Telegram ---
def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML', disable_web_page_preview=False)

# --- 7. Main Signal Logic ---
def main():
    for asset in ASSETS.keys():
        news_items = fetch_news(asset)
        for news in news_items:
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

            df = yf.download(detected_asset, period="2d", interval="1h")
            entry = round(df['Close'][-1], 4) if not df.empty else 0
            sl = round(entry + atr, 4) if signal == "BUY" else round(entry - atr, 4)
            tp = round(entry + 2 * atr, 4) if signal == "BUY" else round(entry - 2 * atr, 4)

            explanation = (
                f"The asset is approaching an important pivot point {entry}\n"
                f"Bias – {bias}"
            )

            message = format_telegram_message(
                detected_asset, signal, explanation, sl, tp, news
            )
            send_telegram_message(message)
            print(f"Signal sent for {detected_asset}: {signal} at {entry}")

if __name__ == "__main__":
    main()
