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
from news_dedup import NewsDeduplicator  # ✅ NEW: import dedup class

# --- Load environment variables ---
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Init deduplication (60 min expiry) ---
dedup = NewsDeduplicator(cache_file="news_sent_cache.json", expiry_minutes=60)

# --- RSS Feeds ---
RSS_FEEDS = [
    "https://www.forexfactory.com/ff_calendar_thisweek.xml",
    "https://www.forexlive.com/feed/",
    "https://www.investing.com/rss/news_25.rss",
    "https://tradingeconomics.com/calendar.rss",
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
    print("[NEWS] Fetching headlines and analyzing...")
    sent_count = 0
    for rss in RSS_FEEDS:
        feed = feedparser.parse(rss)
        for entry in feed.entries[:7]:
            headline = entry.title.strip()
            url = entry.get("link", "").strip() or headline
            date = entry.get("published", entry.get("updated", ""))
            dt = ''
            if date:
                try:
                    dt = str(datetime(*entry.published_parsed[:6]))
                except Exception:
                    dt = date

            # ✅ SKIP if already sent
            if dedup.already_sent(headline, url):
                print(f"[SKIP] Duplicate: {headline}")
                continue

            logic = analyze_news_headline(headline)
            if not logic:
                continue

            alert_lines = [f"*{headline}* ({dt})", url]
            for result in logic:
                alert_lines.append(
                    f" - {result['asset']}: {result['signal']} (score={result['score']}) | {result['reason']}"
                )
            alert_msg = '\n'.join(alert_lines)
            send_telegram_message(alert_msg)
            dedup.mark_sent(headline, url)
            sent_count += 1
    print(f"[NEWS] Sent {sent_count} news alerts.")
    return sent_count

# --- Main/Run Once ---
if __name__ == "__main__":
    fetch_and_analyze_feeds()
