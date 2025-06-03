# auto_alert_scheduler.py

import asyncio
import datetime
from telegramsender import send_telegram_message
from news_feeds import fetch_all_headlines, analyze_all_feeds
from patterns_module import scan_all_patterns  # This is your pattern alerts module
from confirmation_filter import confirmation_filter

TELEGRAM_CHAT_ID = None  # Fill with int or import from env

ALERT_INTERVAL = 60 * 60  # seconds (e.g., every hour)
PATTERNS_TO_WATCH = ["EURUSD", "GBPUSD", "USDJPY"]

async def auto_send_alerts():
    while True:
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        # News alert
        headlines = fetch_all_headlines()
        news_signals, _ = analyze_all_feeds()
        # Pattern alert
        pattern_signals = scan_all_patterns(PATTERNS_TO_WATCH)
        # Logic confirmation (example)
        for signal in news_signals:
            asset = signal.get("asset")
            action = signal.get("signal")
            reason = signal.get("reason")
            # Example: combine with pattern detection
            pattern_alert = any(p['symbol'] == asset and p['signal'] == action for p in pattern_signals)
            if confirmation_filter(True, pattern_alert):  # Always True for news, plus pattern
                msg = (
                    f"[{now}] ALERT: {asset}\n"
                    f"Signal: {action}\n"
                    f"Reason: {reason}\n"
                    f"Pattern Confirmed: {pattern_alert}"
                )
                await send_telegram_message(msg, chat_id=TELEGRAM_CHAT_ID)
        await asyncio.sleep(ALERT_INTERVAL)

# For standalone test
if __name__ == "__main__":
    asyncio.run(auto_send_alerts())
