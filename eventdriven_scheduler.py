# eventdriven_scheduler.py (create this file manually in your project)

import asyncio
from datetime import datetime
from telegramalert import send_pattern_alerts, send_news_and_events

MAJOR_EVENTS_HOURS_UTC = [
    (6, 10),   # London session
    (12, 16),  # NY session
]

def is_market_active():
    now = datetime.utcnow().hour
    return any(start <= now < end for start, end in MAJOR_EVENTS_HOURS_UTC)

async def monitor_major_events():
    symbols = ["EURUSD", "XAUUSD", "US30"]
    timeframes = ["H1"]

    while True:
        if is_market_active():
            for symbol in symbols:
                for tf in timeframes:
                    send_pattern_alerts(symbol, tf)
                    send_news_and_events(symbol)
        else:
            print("[INFO] Market inactive. Skipping scan.")

        await asyncio.sleep(900)  # 15 min

if __name__ == "__main__":
    asyncio.run(monitor_major_events())
