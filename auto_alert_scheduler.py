# autoalert_scheduler.py

import asyncio
import datetime
from telegramsender import send_telegram_message
from news_feeds import fetch_all_headlines, analyze_all_feeds
from patterns_module import scan_all_patterns
from confirmation_filter import confirmation_filter

TELEGRAM_CHAT_ID = None  # Replace this with your actual Telegram chat ID or import from .env

ALERT_INTERVAL = 60 * 60  # check every 1 hour
PATTERNS_TO_WATCH = ["EURUSD", "GBPUSD", "USDJPY"]

async def auto_send_alerts():
    while True:
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        
        headlines = fetch_all_headlines()
        news_signals, _ = analyze_all_feeds()
        pattern_signals = scan_all_patterns(PATTERNS_TO_WATCH)
        
        for signal in news_signals:
            asset = signal.get("asset")
            action = signal.get("signal")
            reason = signal.get("reason")

            pattern_match = any(p['symbol'] == asset and p['signal'] == action for p in pattern_signals)
            
            if confirmation_filter(True, pattern_match):
                msg = (
                    f"[{now}] ✅ ALERT: {asset}\n"
                    f"📈 Signal: {action}\n"
                    f"🧠 Reason: {reason}\n"
                    f"🔍 Pattern Confirmed: {pattern_match}"
                )
                await send_telegram_message(msg, chat_id=TELEGRAM_CHAT_ID)
        
        await asyncio.sleep(ALERT_INTERVAL)

# Standalone testing
if __name__ == "__main__":
    asyncio.run(auto_send_alerts())
