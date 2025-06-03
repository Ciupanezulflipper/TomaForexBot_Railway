# sessions.py
from datetime import datetime, time

def get_market_session(now_utc=None):
    if now_utc is None:
        now_utc = datetime.utcnow().time()
    sessions = [
        ("Tokyo", time(23,0), time(8,0)),
        ("London", time(8,0), time(17,0)),
        ("New York", time(13,0), time(22,0))
    ]
    for name, start, end in sessions:
        if start < end:
            if start <= now_utc <= end:
                return name
        else:  # overnight session (Tokyo)
            if now_utc >= start or now_utc <= end:
                return name
    return "Closed"
