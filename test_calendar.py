from economic_calendar_module import fetch_major_events

events = fetch_major_events(hours_back=6, hours_forward=12)
if not events:
    print("No high-impact macro news/events in the past 6h or next 12h.")
else:
    print("High-impact macro events found:")
    for e in events[:10]:
        print(f"{e['date']} | {e['event']} | Impact: {e['impact']} | Affected: {e['affected']} | Source: {e['source']}")
