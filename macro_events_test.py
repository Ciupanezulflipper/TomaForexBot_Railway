# macro_events_test.py

from economic_calendar_module import fetch_major_events
import pandas as pd

now = pd.Timestamp.utcnow().replace(tzinfo=None)
lookback = now - pd.Timedelta(hours=6)
lookahead = now + pd.Timedelta(hours=12)
events = fetch_major_events()

def safe_to_datetime(dtstr):
    try:
        return pd.to_datetime(dtstr).replace(tzinfo=None)
    except Exception:
        return now  # fallback if parse fails

filtered = [e for e in events if lookback <= safe_to_datetime(e['date']) <= lookahead]

if not filtered:
    print("No high-impact macro news/events in the past 6h or next 12h.")
else:
    for e in filtered[:8]:  # Show up to 8 events for clarity
        print(f"{e['date']} | {e['event']} | Impact: {e['impact']}")
        print(f"Affected: {e['affected']}")
        print(f"Source: {e['source']}")
        print("---")

