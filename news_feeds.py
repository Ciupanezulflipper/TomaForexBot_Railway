# news_feeds.py
from economic_calendar_module import fetch_major_events
import feedparser
import datetime
from news_signal_logic import analyze_news_headline

# Main news and forum sources
RSS_FEEDS = [
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "https://www.investing.com/rss/news_301.rss",
    "https://www.fxstreet.com/rss/news",
    "https://www.forexlive.com/feed/news/",
    "https://tradingeconomics.com/calendar/rss",
    "https://www.reutersagency.com/feed/?best-topics=markets&post_type=best",
    "https://www.bloomberg.com/feed/podcast/etf-report.xml",
    "https://www.financialjuice.com/rss/news"
]
REDDIT_SUBS = ["Forex", "StockMarket", "CryptoCurrency", "Economics", "wallstreetbets"]

X_ENABLED = False   # Twitter/X
TG_ENABLED = False  # Telegram

UPCOMING_EVENTS = [
    {"date": "2024-06-12", "event": "US CPI Release", "impact": "High", "pair": "USD, US30, Gold", "effect": "Volatile, USD strength/weakness"},
    {"date": "2024-06-19", "event": "FOMC Meeting", "impact": "High", "pair": "USD, US30, Gold", "effect": "Fed rates, USD direction, risk-on/off"},
    {"date": "2024-07-09", "event": "Trump Tariff Decision", "impact": "High", "pair": "US30, USD, EURUSD", "effect": "Risk sentiment, tariffs, stock/bond move"},
]
def fetch_rss_headlines():
    headlines = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.get('title', '').strip()
                published = entry.get('published', '') or entry.get('pubDate', '')
                link = entry.get('link', '')
                headlines.append((published, title, link))
        except Exception as ex:
            print(f"[RSS ERROR] {url}: {ex}")
    return headlines

def fetch_reddit_headlines():
    try:
        import requests
    except ImportError:
        print("[Reddit] requests lib missing!")
        return []
    headlines = []
    for sub in REDDIT_SUBS:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
        headers = {'User-agent': 'Mozilla/5.0'}
        try:
            r = requests.get(url, headers=headers, timeout=8)
            posts = r.json().get("data", {}).get("children", [])
            for p in posts:
                title = p['data'].get('title', '')
                ts = p['data'].get('created_utc', 0)
                dt = datetime.datetime.utcfromtimestamp(ts)
                link = 'https://reddit.com' + p['data'].get('permalink', '')
                if title:
                    headlines.append((dt.strftime("%Y-%m-%d %H:%M"), title, link))
        except Exception as ex:
            print(f"[Reddit ERROR] {sub}: {ex}")
    return headlines

def fetch_x_headlines():
    print("[X] Twitter scraping not yet enabled.")
    return []

def fetch_telegram_headlines():
    print("[TG] Telegram group fetching not yet enabled.")
    return []

def fetch_all_headlines():
    """Returns all headlines from all sources, combined (RSS, Reddit, X, TG)."""
    all_headlines = []
    all_headlines += fetch_rss_headlines()
    all_headlines += fetch_reddit_headlines()
    if X_ENABLED:
        all_headlines += fetch_x_headlines()
    if TG_ENABLED:
        all_headlines += fetch_telegram_headlines()
    return all_headlines

def fetch_upcoming_events():
    today = datetime.date.today()
    out = []
    for event in UPCOMING_EVENTS:
        try:
            e_date = datetime.datetime.strptime(event['date'], "%Y-%m-%d").date()
            if e_date >= today:
                out.append(event)
        except Exception:
            continue
    return out

def analyze_all_feeds():
    all_headlines = fetch_all_headlines()
    logic_alerts = []
    for (published, title, link) in all_headlines:
        logic = analyze_news_headline(title)
        for signal in logic:
            sig = signal if isinstance(signal, dict) else (signal[0] if isinstance(signal, (tuple, list)) and len(signal) > 0 and isinstance(signal[0], dict) else {})
            logic_alerts.append({
                'published': published,
                'headline': title,
                'link': link,
                'asset': sig.get('asset', '-'),
                'signal': sig.get('signal', '-'),
                'score': sig.get('score', '-'),
                'reason': sig.get('reason', '-')
            })
    try:
        events = fetch_major_events()
    except Exception:
        events = fetch_upcoming_events()
    return logic_alerts, events

if __name__ == "__main__":
    print("[NEWS] Fetching and analyzing ALL sources...")
    logic_alerts, events = analyze_all_feeds()
    for a in logic_alerts[:20]:
        print(f"- {a['published'][:16]}: {a['headline']} => {a['asset']} {a['signal']} (reason: {a['reason']})")
    if events:
        print("\n[UPCOMING EVENTS]")
        for e in events:
            print(f"- {e['date']}: {e['event']} [{e['impact']}] | {e.get('pair', '-')} | Effect: {e.get('effect', '-')}")
if __name__ == "__main__":
    print("[TEST] Checking all RSS feed connections...")

    from time import sleep
    ok_count = 0
    for url in RSS_FEEDS:
        print(f"\n--- Checking: {url}")
        try:
            feed = feedparser.parse(url)
            titles = [entry.get('title', '') for entry in feed.entries]
            if not titles:
                print(f"  [WARNING] No entries found.")
            else:
                print(f"  [OK] {len(titles)} entries. Example: {titles[0][:90]}")
                ok_count += 1
        except Exception as e:
            print(f"  [ERROR] Could not fetch: {e}")
        sleep(1)  # Not required, but polite for rate-limiting

    print(f"\nResult: {ok_count}/{len(RSS_FEEDS)} feeds returned entries.")

