import os
import requests
from telegram import Update
from telegram.ext import ContextTypes

def test_finnhub_connection():
    api_key = os.getenv("FINNHUB_API_KEY")
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200 and resp.json():
            return True
    except Exception:
        pass
    return False

# KEEP ONLY THIS VERSION:
def fetch_finnhub_news(symbol, max_results=5):
    api_key = os.getenv("FINNHUB_API_KEY")
    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-05-01&to=2025-06-01&token={api_key}"
    try:
        print(f"[DEBUG] Requesting: {url}")
        resp = requests.get(url, timeout=5)
        print(f"[DEBUG] Response code: {resp.status_code}")
        data = resp.json()
        print(f"[DEBUG] Response data: {data[:2]}")
        headlines = []
        for item in data[:max_results]:
            headlines.append({
                "title": item.get("headline", ""),
                "publisher": item.get("source", ""),
                "link": item.get("url", ""),
            })
        return headlines
    except Exception as e:
        print(f"[ERROR] Exception in fetch_finnhub_news: {e}")
        return [{"title": f"Failed to fetch Finnhub news: {e}", "publisher": "", "link": ""}]

def score_sentiment(text):
    pos = ["up", "beat", "surge", "record", "positive", "strong", "gain", "growth"]
    neg = ["down", "miss", "loss", "weak", "decline", "negative", "drop", "cut", "crash"]
    text = text.lower()
    score = 0
    for w in pos:
        if w in text:
            score += 1
    for w in neg:
        if w in text:
            score -= 1
    if score > 0:
        return "📈 Positive"
    elif score < 0:
        return "📉 Negative"
    else:
        return "➡️ Neutral"

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[DEBUG] /news command called")
    if not context.args:
        print("[DEBUG] No symbol argument provided")
        await update.message.reply_text("⚠️ Usage: /news SYMBOL (e.g. /news TSLA)")
        return
    symbol = context.args[0].upper()
    print(f"[DEBUG] Symbol requested: {symbol}")  
    await update.message.reply_text(f"📰 Fetching news for {symbol} ...")
    headlines = fetch_finnhub_news(symbol)
    print(f"[DEBUG] Headlines fetched: {len(headlines)}") 
    if not headlines or all(not h["title"] for h in headlines):
        print("[DEBUG] No headlines found or all empty")
        await update.message.reply_text("❌ No news found.")
        return

    msg = f"<b>Latest news for {symbol}:</b>\n\n"
    for i, headline in enumerate(headlines, 1):
        sentiment = score_sentiment(headline["title"])
        msg += f"{i}. {sentiment}\n<b>{headline['title']}</b>\n"
        msg += f"<i>Source:</i> {headline['publisher']}\n"
        if headline["link"]:
            msg += f"<a href='{headline['link']}'>Read more</a>\n"
        msg += "\n"
    print(f"[DEBUG] Final message length: {len(msg)}")     
    await update.message.reply_text(msg, parse_mode="HTML")
    print("[DEBUG] Message sent to Telegram") 
def get_news_sentiment(symbol):
    """
    Simple function to return the overall sentiment for the latest news headlines for a symbol.
    Returns: "Positive", "Negative" or "Neutral" based on scoring all headlines.
    """
    headlines = fetch_finnhub_news(symbol, max_results=5)
    scores = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for h in headlines:
        label = score_sentiment(h["title"])
        if "Positive" in label:
            scores["Positive"] += 1
        elif "Negative" in label:
            scores["Negative"] += 1
        else:
            scores["Neutral"] += 1
    # Majority logic
    if scores["Positive"] > scores["Negative"]:
        return "BULLISH"
    elif scores["Negative"] > scores["Positive"]:
        return "BEARISH"
    else:
        return "NEUTRAL"

