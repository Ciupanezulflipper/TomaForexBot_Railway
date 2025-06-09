import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Define basic keywords to check polarity
BULLISH_WORDS = ['surge', 'rally', 'bullish', 'gain', 'strong', 'beat']
BEARISH_WORDS = ['plunge', 'drop', 'bearish', 'fall', 'weak', 'miss']

# === Simple News Sentiment Classifier ===
def classify_sentiment(text):
    text_lower = text.lower()
    score = 0
    for word in BULLISH_WORDS:
        if word in text_lower:
            score += 1
    for word in BEARISH_WORDS:
        if word in text_lower:
            score -= 1
    if score > 0:
        return 'BULLISH'
    elif score < 0:
        return 'BEARISH'
    return 'NEUTRAL'

def get_news_sentiment(symbol):
    try:
        if not NEWS_API_KEY:
            return 'NEUTRAL'
        response = requests.get(
            f"https://newsapi.org/v2/everything?q={symbol}&apiKey={NEWS_API_KEY}&pageSize=5"
        )
        if response.status_code != 200:
            logging.warning(f"[NEWS] Failed to fetch: {response.text}")
            return 'NEUTRAL'
        articles = response.json().get("articles", [])
        sentiment_score = 0
        for article in articles:
            title = article.get("title", "")
            sentiment = classify_sentiment(title)
            if sentiment == 'BULLISH':
                sentiment_score += 1
            elif sentiment == 'BEARISH':
                sentiment_score -= 1
        if sentiment_score > 0:
            return 'BULLISH'
        elif sentiment_score < 0:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    except Exception as e:
        logging.error(f"[NEWS] Error getting sentiment for {symbol}: {e}")
        return 'NEUTRAL'

# === Telegram Command ===
from telegram import Update
from telegram.ext import ContextTypes

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /news SYMBOL")
        return
    symbol = context.args[0].upper()
    sentiment = get_news_sentiment(symbol)
    await update.message.reply_text(f"📰 News Sentiment for {symbol}: {sentiment}")
