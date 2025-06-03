# economic_calendar_module.py
# Multi-source Economic Calendar for Major FX Events

import requests
from datetime import datetime, timedelta
import pandas as pd
import feedparser

CALENDAR_SOURCES = [
    'https://nfs.faireconomy.media/ff_calendar_thisweek.xml',  # ForexFactory RSS for this week
    'https://www.forexlive.com/feed/news/',                   # ForexLive News RSS
    'https://tradingeconomics.com/calendar/rss',              # TradingEconomics Economic Calendar
]

IMPORTANT_KEYWORDS = [
    'Fed', 'FOMC', 'interest rate', 'NFP', 'payroll', 'CPI', 'inflation', 'ECB',
    'BOE', 'BOJ', 'RBA', 'GDP', 'PMI', 'unemployment', 'jobs', 'PPI', 'central bank',
]

PAIR_MAP = {
    'USD': ['EURUSD', 'USDJPY', 'GBPUSD', 'US30', 'SPX500'],
    'EUR': ['EURUSD', 'EURAUD', 'EURJPY', 'DAX'],
    'GBP': ['GBPUSD', 'EURGBP', 'GBPJPY', 'FTSE'],
    'JPY': ['USDJPY', 'EURJPY', 'GBPJPY', 'NIKKEI'],
    'AUD': ['AUDUSD', 'EURAUD', 'AUDJPY'],
    'CAD': ['USDCAD', 'EURCAD'],
    'CHF': ['USDCHF', 'EURCHF'],
    # Add more as needed
}

def parse_rss_date(date_str):
    """Robust date parsing for RSS feeds."""
    for fmt in ["%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y", "%Y-%m-%dT%H:%M:%SZ"]:
        try:
            return datetime.strptime(date_str[:len(fmt)], fmt)
        except Exception:
            continue
    return datetime.utcnow()

def fetch_all_calendar():
    entries = []
    for url in CALENDAR_SOURCES:
        try:
            feed = feedparser.parse(url)
            for item in feed.entries:
                title = getattr(item, 'title', '')
                summary = getattr(item, 'summary', '')
                published = getattr(item, 'published', getattr(item, 'updated', ''))
                dt = parse_rss_date(published) if published else datetime.utcnow()
                entries.append({
                    'title': title,
                    'summary': summary,
                    'datetime': dt,
                    'source': url.split("/")[2],
                })
        except Exception as e:
            print(f"[WARN] Could not parse {url}: {e}")
    return entries

def analyze_events(entries):
    """Filter only big-impact events, map to pairs/markets."""
    results = []
    for e in entries:
        text = (e['title'] + ' ' + e['summary']).lower()
        score = 0
        for k in IMPORTANT_KEYWORDS:
            if k.lower() in text:
                score += 1
        if score == 0:
            continue  # Not important
        # Map to pairs
        affected = []
        for k, v in PAIR_MAP.items():
            if k.lower() in text:
                affected.extend(v)
        if not affected:
            affected = ['ALL MAJORS']
        results.append({
            'event': e['title'],
            'date': e['datetime'].strftime('%Y-%m-%d %H:%M'),
            'impact': score,
            'affected': ', '.join(set(affected)),
            'source': e['source'],
        })
    # Sort by date, impact desc
    results.sort(key=lambda x: (x['date'], -x['impact']))
    return results

def fetch_major_events(hours_back=6, hours_forward=12):
    """Fetch and return list of major economic events in a given time window."""
    all_events = fetch_all_calendar()
    now = datetime.utcnow()
    lookback = now - timedelta(hours=hours_back)
    lookahead = now + timedelta(hours=hours_forward)
    filtered = []
    for e in analyze_events(all_events):
        event_dt = pd.to_datetime(e['date'])
        # Remove timezone info for safe comparison
        if event_dt.tzinfo is not None:
            event_dt = event_dt.tz_localize(None)
        if lookback <= event_dt <= lookahead:
            filtered.append(e)
    return filtered

# CLI test
if __name__ == "__main__":
    print("[ECONOMIC CALENDAR] Fetching major events from all sources...")
    major_events = fetch_major_events(hours_back=6, hours_forward=12)
    if not major_events:
        print("No major events found.")
    else:
        for e in major_events:
            print(f"{e['date']} | {e['event']} | Impact: {e['impact']} | Affected: {e['affected']} | Source: {e['source']}")
