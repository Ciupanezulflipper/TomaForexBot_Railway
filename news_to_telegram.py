# news_to_telegram.py

import os
from dotenv import load_dotenv
import pandas as pd

from news_feeds import fetch_all_headlines, analyze_all_feeds
from news_signal_logic import analyze_news_headline
from multi_layer_confirmation import multi_layer_confirmation
from telegramsender import send_telegram_message
from news_dedup import NewsDeduplicator  # ✅ NEW

load_dotenv()
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# ✅ Dedup setup (1 day cache)
dedup = NewsDeduplicator(cache_file="news_sent_cache.json", expiry_minutes=1440)

def run_news_signal_pipeline():
    print("[NEWS2TG] Fetching and processing all news feeds...")
    headlines = fetch_all_headlines()
    news_signals = []
    alert_msgs = []

    for headline in headlines:
        title = headline.get("title") if isinstance(headline, dict) else str(headline)
        url = headline.get("link") if isinstance(headline, dict) else ""

        if dedup.already_sent(title, url):
            print(f"[SKIP] Already sent: {title}")
            continue

        signals = analyze_news_headline(title)
        if signals:
            news_signals.extend(signals)
            dedup.mark_sent(title, url)

    if not news_signals:
        print("[NEWS2TG] No new actionable news signals.")
        return

    # Mocked technical data (replace with real analysis result)
    df = pd.DataFrame([{
        "score": 4,
        "pattern": "Bullish Engulfing",
        "ema9": 1.12,
        "ema21": 1.11,
        "rsi": 41,
        "symbol": "EURUSD"
    }])

    # Multi-layer confirmation
    confirmation = multi_layer_confirmation(df, news_signals)
    msg = "[NEWS ALERT]\n"
    msg += "\n".join(f"{s['asset']}: {s['signal']} ({s['reason']})" for s in news_signals)
    msg += f"\n\n[Confirmation]: {confirmation['reason']}"

    print(msg)
    send_telegram_message(msg, chat_id=TELEGRAM_CHAT_ID)

if __name__ == "__main__":
    run_news_signal_pipeline()
