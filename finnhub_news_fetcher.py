# finnhub_news_fetcher.py (update with manual .env load)

import os
import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import from news_cache
from news_cache import load_cache, save_cache, add_to_cache, is_article_sent, clean_cache

# ✅ Manually load .env for standalone script testing
load_dotenv()
API_KEY = os.getenv("FINNHUB_API_KEY")
NEWS_CACHE_EXPIRY_HOURS = 72 # Can be configured elsewhere if needed

# Counter for probabilistic cache cleaning, if desired
# For simplicity, we'll clean cache on each call for now, or once at startup in a real app.
# CLEAN_CACHE_INTERVAL = 10 # Clean every 10 calls
# call_count = 0

async def fetch_recent_forex_news(hours_ago: int = 6, max_articles_to_return: int = 5):
    # global call_count # Needed if using probabilistic cleaning
    if not API_KEY:
        print("[⚠️] FINNHUB_API_KEY not set — skipping news fetch.")
        return []

    news_cache = load_cache()
    
    # Basic cache cleaning (can be done less frequently in a production system)
    # call_count += 1
    # if call_count % CLEAN_CACHE_INTERVAL == 0:
    #     pruned_count = clean_cache(news_cache, expiry_hours=NEWS_CACHE_EXPIRY_HOURS)
    #     if pruned_count > 0:
    #         save_cache(news_cache) # Save after cleaning if changes were made
    # For this task, let's try cleaning more directly if it's not too frequent.
    # Or, even better, let's assume cleaning is handled by a separate scheduled task or less frequently.
    # For now, to ensure it's part of the flow, let's include it.
    # A simple approach: clean_cache might be too slow if called every time.
    # Let's just load and save, and recommend cleaning be done by a separate scheduled job.
    # For the purpose of this task, we will add it here and it can be optimized later.
    
    # Let's clean the cache once at the beginning of the function call.
    # This is not optimal for high-frequency calls but fulfills the requirement.
    if clean_cache(news_cache, expiry_hours=NEWS_CACHE_EXPIRY_HOURS) > 0:
        save_cache(news_cache) # Save if cleaning removed items


    try:
        url = f"https://finnhub.io/api/v1/news?category=forex&token={API_KEY}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status() # Raise an exception for HTTP errors
                data = await response.json()
                if not isinstance(data, list):
                    print(f"[ERROR] Finnhub API did not return a list: {data}")
                    return []


        # Filter by date first (as in original code)
        cutoff_datetime = datetime.utcnow() - timedelta(hours=hours_ago)
        
        # Process articles from Finnhub (they are generally sorted by recency)
        potential_articles = []
        for n in data:
            if 'datetime' in n and n.get('url'): # Ensure 'url' and 'datetime' exist
                article_timestamp = datetime.utcfromtimestamp(n['datetime'])
                if article_timestamp > cutoff_datetime:
                    potential_articles.append(n)
            if len(potential_articles) >= 20: # Process a bit more than needed to find new ones
                break
        
        new_articles_to_return = []
        cache_updated = False
        for article in potential_articles:
            article_url = article.get("url")
            # Ensure URL is valid before checking/adding
            if not article_url:
                print(f"[⚠️] Article found with no URL: {article.get('headline', 'N/A')}")
                continue

            if not is_article_sent(article_url, news_cache):
                if len(new_articles_to_return) < max_articles_to_return:
                    new_articles_to_return.append(article)
                add_to_cache(article_url, news_cache) # Add to cache even if it exceeds max_to_return for this run
                cache_updated = True
            
            # Stop if we have enough new articles for this run
            if len(new_articles_to_return) >= max_articles_to_return:
                break 
        
        if cache_updated:
            save_cache(news_cache)

        return new_articles_to_return # Return only new articles, up to the limit

    except aiohttp.ClientError as e:
        print(f"[ERROR] AIOHTTP error fetching news from Finnhub: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Failed to fetch or process news from Finnhub: {e} (Data: {data if 'data' in locals() else 'N/A'})")
        return []

if __name__ == "__main__":
    import asyncio
    async def test():
        print("--- First fetch ---")
        articles1 = await fetch_recent_forex_news(hours_ago=24)
        if articles1:
            for a in articles1:
                print(f"📰 {a.get('headline')}\n🔗 {a.get('url')}\n")
        else:
            print("No articles returned on first fetch.")

        print("\n--- Second fetch (should ideally return no new articles or different ones if time passed) ---")
        articles2 = await fetch_recent_forex_news(hours_ago=24)
        if articles2:
            for a in articles2:
                print(f"📰 {a.get('headline')}\n🔗 {a.get('url')}\n")
        else:
            print("No new articles returned on second fetch (as expected if no new news).")
        
        print("\n--- Test with a very old article (simulating it's now out of 'hours_ago' window) ---")
        # This part of the test mainly ensures the function runs.
        # The cache logic prevents re-sending, time window logic prevents old news.
        # To truly test cache expiry, one would need to manipulate cache file timestamps or wait.
        # For now, the main test is the repeat call.
        
        # Clean up dummy cache if tests were run using main CACHE_FILE
        # For __main__ tests, it's better to use a temporary cache file.
        # However, the provided news_cache uses a fixed name.
        # Consider adding a parameter to news_cache functions for the cache file path for easier testing.

    asyncio.run(test())
