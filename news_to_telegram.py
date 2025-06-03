# news_to_telegram.py

import os
from dotenv import load_dotenv
import pandas as pd

from news_feeds import fetch_all_headlines, analyze_all_feeds
from news_signal_logic import analyze_news_headline
from multi_layer_confirmation import multi_layer_confirmation
from telegramsender import send_telegram_message

load_dotenv()
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

def run_news_signal_pipeline():
    print("[NEWS2TG] Fetching and processing all news feeds...")
    headlines = fetch_all_headlines()
    news_signals = []
    alert_msgs = []
    for headline in headlines:
        signals = analyze_news_headline(headline)
        news_signals.extend(signals)

    # Combine with technical (example, can be real DataFrame from your bot)
    # For demo, use a fake DataFrame for EURUSD
    # In practice: replace with actual analyze_symbol output!
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
