# news_feeds.py
from economic_calendar_module import fetch_major_events
import feedparser
import datetime
from news_signal_logic import analyze_news_headline
import os # For potential path joining if cache file needs it, not directly used for cache logic here
import json # For Reddit JSON parsing error handling

# Import from news_cache
from news_cache import load_cache, save_cache, add_to_cache, is_article_sent, clean_cache

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

UPCOMING_EVENTS = [ # This seems like static data, not directly affected by news cache
    {"date": "2024-06-12", "event": "US CPI Release", "impact": "High", "pair": "USD, US30, Gold", "effect": "Volatile, USD strength/weakness"},
    {"date": "2024-06-19", "event": "FOMC Meeting", "impact": "High", "pair": "USD, US30, Gold", "effect": "Fed rates, USD direction, risk-on/off"},
    {"date": "2024-07-09", "event": "Trump Tariff Decision", "impact": "High", "pair": "US30, USD, EURUSD", "effect": "Risk sentiment, tariffs, stock/bond move"},
]

NEWS_CACHE_EXPIRY_HOURS = 72 # Or from a central config

def fetch_rss_headlines(news_cache, cache_updated_flags):
    """Fetches RSS headlines, filters against cache, and updates cache."""
    new_headlines = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.get('title', '').strip()
                published_str = entry.get('published', '') or entry.get('pubDate', '')
                link = entry.get('link', '')

                if not link: # Skip if no link, as it's our cache key
                    print(f"[RSS WARN] Entry without link in {url}: {title[:50]}")
                    continue

                if not is_article_sent(link, news_cache):
                    new_headlines.append({'published': published_str, 'title': title, 'link': link, 'source': 'RSS'})
                    add_to_cache(link, news_cache)
                    cache_updated_flags.append(True)
        except Exception as ex:
            print(f"[RSS ERROR] {url}: {ex}")
    return new_headlines

def fetch_reddit_headlines(news_cache, cache_updated_flags):
    """Fetches Reddit headlines, filters against cache, and updates cache."""
    try:
        import requests
    except ImportError:
        print("[Reddit] requests lib missing!")
        return []
    
    new_headlines = []
    headers = {'User-agent': 'Mozilla/5.0'} # Define headers once
    for sub in REDDIT_SUBS:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
        try:
            r = requests.get(url, headers=headers, timeout=8)
            r.raise_for_status() # Check for HTTP errors
            posts = r.json().get("data", {}).get("children", [])
            for p in posts:
                data = p.get('data', {})
                title = data.get('title', '')
                ts = data.get('created_utc', 0)
                permalink = data.get('permalink', '')
                
                if not title or not permalink: # Skip if essential data missing
                    continue

                # Construct full link for Reddit post
                link = 'https://reddit.com' + permalink
                dt_published = datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

                if not is_article_sent(link, news_cache):
                    new_headlines.append({'published': dt_published, 'title': title, 'link': link, 'source': f'Reddit r/{sub}'})
                    add_to_cache(link, news_cache)
                    cache_updated_flags.append(True)
        except requests.RequestException as ex:
            print(f"[Reddit Request ERROR] {sub}: {ex}")
        except json.JSONDecodeError as ex:
            print(f"[Reddit JSON ERROR] {sub}: {ex}")
        except Exception as ex: # Catch any other unexpected errors
            print(f"[Reddit UNKNOWN ERROR] {sub}: {ex}")
    return new_headlines

def fetch_x_headlines(news_cache, cache_updated_flags): # Pass cache for future use
    print("[X] Twitter scraping not yet enabled.")
    return []

def fetch_telegram_headlines(news_cache, cache_updated_flags): # Pass cache for future use
    print("[TG] Telegram group fetching not yet enabled.")
    return []

def fetch_all_headlines():
    """Returns all NEW headlines from all sources, combined (RSS, Reddit, X, TG)."""
    news_cache = load_cache()
    cache_updated_flags = [] # Use a list to track if any sub-function updated cache

    # Clean cache once at the beginning
    if clean_cache(news_cache, expiry_hours=NEWS_CACHE_EXPIRY_HOURS) > 0:
        cache_updated_flags.append(True) # Mark as updated if cleaning occurred

    all_new_headlines = []
    
    # Pass the cache and the list to track updates
    all_new_headlines.extend(fetch_rss_headlines(news_cache, cache_updated_flags))
    all_new_headlines.extend(fetch_reddit_headlines(news_cache, cache_updated_flags))
    
    if X_ENABLED:
        all_new_headlines.extend(fetch_x_headlines(news_cache, cache_updated_flags))
    if TG_ENABLED:
        all_new_headlines.extend(fetch_telegram_headlines(news_cache, cache_updated_flags))
    
    if cache_updated_flags: # If the list is not empty, it means an update happened
        save_cache(news_cache)
        print(f"[Cache] News cache saved by fetch_all_headlines. Found {len(all_new_headlines)} new articles.")
    else:
        print(f"[Cache] No cache updates in fetch_all_headlines. Found {len(all_new_headlines)} new articles (could be 0 if all seen).")

    # Return structure changed to list of dicts for easier use in analyze_all_feeds
    return all_new_headlines 

def fetch_upcoming_events(): # No changes needed here
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
    """Analyzes all NEW headlines and combines with economic events."""
    # fetch_all_headlines now returns a list of dicts, each with 'title', 'link', 'published', 'source'
    all_new_headlines = fetch_all_headlines() 
    
    logic_alerts = []
    if not all_new_headlines:
        print("[Feeds] No new headlines found to analyze.")
    
    for item in all_new_headlines: # Iterate through the list of dicts
        # analyze_news_headline expects just the headline string
        # We might want to pass more context in the future (e.g., source, link)
        # For now, stick to existing interface of analyze_news_headline
        signals_from_headline = analyze_news_headline(item['title']) 
        
        for signal_details in signals_from_headline: # analyze_news_headline seems to return a list of signals
            # Ensure signal_details is a dict, as expected by downstream code
            if isinstance(signal_details, dict):
                logic_alerts.append({
                    'published': item.get('published', 'N/A'),
                    'headline': item['title'],
                    'link': item['link'],
                    'source': item.get('source', 'N/A'), # Add source for better context
                    'asset': signal_details.get('asset', '-'),
                    'signal': signal_details.get('signal', '-'),
                    'score': signal_details.get('score', '-'),
                    'reason': signal_details.get('reason', '-')
                })
            else:
                # This case was in original code, trying to adapt.
                # It implies analyze_news_headline might return list of tuples/lists.
                sig = signal_details if isinstance(signal_details, dict) else \
                      (signal_details[0] if isinstance(signal_details, (tuple, list)) and \
                       len(signal_details) > 0 and isinstance(signal_details[0], dict) else {})
                logic_alerts.append({
                    'published': item.get('published', 'N/A'),
                    'headline': item['title'],
                    'link': item['link'],
                    'source': item.get('source', 'N/A'),
                    'asset': sig.get('asset', '-'),
                    'signal': sig.get('signal', '-'),
                    'score': sig.get('score', '-'),
                    'reason': sig.get('reason', '-')
                })

    try:
        # fetch_major_events might also benefit from caching if it hits external APIs frequently
        # For now, assume it's efficient enough or handled elsewhere.
        events = fetch_major_events() 
    except Exception as e:
        print(f"[Events] Error fetching major events: {e}. Falling back to static list.")
        events = fetch_upcoming_events() # Fallback to static list
        
    return logic_alerts, events

if __name__ == "__main__":
    print("[NEWS_FEEDS TEST] Fetching and analyzing ALL sources (1st run)...")
    logic_alerts1, events1 = analyze_all_feeds()
    if logic_alerts1:
        for a in logic_alerts1[:5]: # Print first 5 new alerts
            print(f"- {a.get('published','N/A')[:16]}: {a['headline'][:70]}... => {a['asset']} {a['signal']} (Source: {a.get('source','N/A')})")
    else:
        print("No new articles found on 1st run.")
        
    if events1:
        print("\n[UPCOMING EVENTS (1st run)]")
        for e in events1[:3]: # Print first 3 events
            print(f"- {e.get('date','N/A')}: {e.get('event','N/A')} [{e.get('impact','N/A')}]")

    print("\n[NEWS_FEEDS TEST] Fetching and analyzing ALL sources (2nd run - expecting fewer or no new articles)...")
    logic_alerts2, events2 = analyze_all_feeds()
    if logic_alerts2:
        for a in logic_alerts2[:5]:
             print(f"- {a.get('published','N/A')[:16]}: {a['headline'][:70]}... => {a['asset']} {a['signal']} (Source: {a.get('source','N/A')})")
    else:
        print("No new articles found on 2nd run (this is expected if no new external news).")

    # The RSS feed connection test can remain as is, it's for checking sources, not cache.
    # Original RSS test code (second if __name__ == "__main__" block was merged into one):
    # print("\n[TEST] Checking all RSS feed connections...")
    # from time import sleep
    # ok_count = 0
    # for url_idx, feed_url_to_check in enumerate(RSS_FEEDS): # Use a different variable name
    #     if url_idx >= 3: # Limit checks in automated test to save time
    #         print(f"Skipping further RSS checks in automated test (checked {url_idx})...")
    #         break
    #     print(f"\n--- Checking: {feed_url_to_check}")
    #     try:
    #         parsed_feed = feedparser.parse(feed_url_to_check) # Use a different variable name
    #         titles = [entry.get('title', '') for entry in parsed_feed.entries]
    #         if not titles:
    #             print(f"  [WARNING] No entries found.")
    #         else:
    #             print(f"  [OK] {len(titles)} entries. Example: {titles[0][:90]}")
    #             ok_count += 1
    #     except Exception as e_rss: # Use a different variable name
    #         print(f"  [ERROR] Could not fetch: {e_rss}")
    #     sleep(1)
    # print(f"\nResult for limited RSS check: {ok_count}/{min(len(RSS_FEEDS), 3)} feeds returned entries.")

