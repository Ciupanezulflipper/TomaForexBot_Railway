# news_feeds_telegram_integration.py
"""
This script fetches news and economic events from multiple RSS sources and sends the impact logic to your Telegram bot/chat automatically.
You need to have your bot token and chat ID set up in your .env file as TELEGRAM_TOKEN and TELEGRAM_CHAT_ID.
"""
import os
import feedparser
import requests
from dotenv import load_dotenv
from datetime import datetime
from news_signal_logic import analyze_news_headline

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- RSS Feeds ---
RSS_FEEDS = [
    "https://www.forexfactory.com/ff_calendar_thisweek.xml",  # ForexFactory Calendar (events)
    "https://www.forexlive.com/feed/",                        # ForexLive News
    "https://www.investing.com/rss/news_25.rss",              # Investing.com Market News
    "https://tradingeconomics.com/calendar.rss",              # TradingEconomics Events
]

# --- Telegram Send Function ---
def send_telegram_message(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[ERROR] Telegram token or chat ID missing!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code != 200:
            print(f"[TELEGRAM] Error: {r.text}")
    except Exception as ex:
        print(f"[TELEGRAM] Exception: {ex}")

# --- Parse and Logic ---
def fetch_and_analyze_feeds():
    all_alerts = []
    print("[NEWS] Fetching headlines and analyzing...")
    for rss in RSS_FEEDS:
        feed = feedparser.parse(rss)
        for entry in feed.entries[:7]:  # Only latest 7 per source
            headline = entry.title
            date = entry.get('published', entry.get('updated', ''))
            dt = ''
            if date:
                try:
                    dt = str(datetime(*entry.published_parsed[:6]))
                except Exception:
                    dt = date
            logic = analyze_news_headline(headline)
            alert_lines = [f"*{headline}* ({dt})"]
            for result in logic:
                alert_lines.append(
                    f" - {result['asset']}: {result['signal']} (score={result['score']}) | {result['reason']}"
                )
            all_alerts.append('\n'.join(alert_lines))
    return all_alerts

# --- Main/Run Once ---
if __name__ == "__main__":
    alerts = fetch_and_analyze_feeds()
    print(f"[NEWS] Sending {len(alerts)} alerts to Telegram...")
    for alert in alerts:
        send_telegram_message(alert)
