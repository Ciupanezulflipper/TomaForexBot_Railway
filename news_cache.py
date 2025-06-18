import json
import time
import os
from datetime import datetime, timedelta

CACHE_FILE = "sent_news_cache.json"
DEFAULT_EXPIRY_HOURS = 72  # Default cache expiry: 3 days

def load_cache(cache_file_path=CACHE_FILE):
    """Loads the cache from a JSON file."""
    if os.path.exists(cache_file_path):
        try:
            with open(cache_file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"[Cache] Error decoding JSON from {cache_file_path}. Returning new cache.")
            return {}
    return {}

def save_cache(cache, cache_file_path=CACHE_FILE):
    """Saves the cache to a JSON file."""
    try:
        with open(cache_file_path, "w") as f:
            json.dump(cache, f, indent=4)
    except IOError as e:
        print(f"[Cache] Error saving cache to {cache_file_path}: {e}")

def add_to_cache(article_url, cache, timestamp=None):
    """Adds an article URL and timestamp to the cache.
    Uses current UTC time if timestamp is not provided.
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    cache[article_url] = timestamp
    # print(f"[Cache] Added to cache: {article_url} @ {timestamp}") # Optional: for debugging

def is_article_sent(article_url, cache):
    """Checks if an article URL is already in the cache."""
    sent = article_url in cache
    # if sent: # Optional: for debugging
        # print(f"[Cache] Article already sent: {article_url}")
    # else: # Optional: for debugging
        # print(f"[Cache] Article is new: {article_url}")
    return sent

def clean_cache(cache, expiry_hours=DEFAULT_EXPIRY_HOURS):
    """Removes articles older than expiry_hours from the cache.
    Returns the number of items pruned.
    """
    if not cache:
        return 0

    pruned_count = 0
    now = datetime.utcnow()
    expiry_delta = timedelta(hours=expiry_hours)
    
    # Create a new dictionary for items to keep
    cleaned_cache_items = {}

    for url, timestamp_str in cache.items():
        try:
            # Ensure timestamp is a string and then parse
            if not isinstance(timestamp_str, str):
                # Try to convert if it's a float (older format compatibility)
                if isinstance(timestamp_str, float):
                    timestamp_dt = datetime.utcfromtimestamp(timestamp_str)
                else: # Skip if format is unknown
                    print(f"[Cache] Skipping entry with unparseable timestamp format: {url} - {timestamp_str}")
                    cleaned_cache_items[url] = timestamp_str # Keep it for now if unsure
                    continue 
            else:
                timestamp_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')) # Handle Z for UTC

            if now - timestamp_dt < expiry_delta:
                cleaned_cache_items[url] = timestamp_str
            else:
                # print(f"[Cache] Pruning old article: {url}") # Optional: for debugging
                pruned_count += 1
        except ValueError as e:
            print(f"[Cache] Error parsing timestamp for URL {url} ('{timestamp_str}'): {e}. Keeping entry.")
            # If parsing fails, keep the entry to be safe, or decide on a stricter removal policy
            cleaned_cache_items[url] = timestamp_str


    # Update the original cache dictionary with the cleaned items
    cache.clear()
    cache.update(cleaned_cache_items)
    
    if pruned_count > 0:
        print(f"[Cache] Pruned {pruned_count} old articles from cache.")
    
    return pruned_count

if __name__ == "__main__":
    # Test the cache functions
    test_cache = load_cache("test_cache.json")
    print(f"Initial cache: {test_cache}")

    article1_url = "http://example.com/article1"
    article2_url = "http://example.com/article2"

    if not is_article_sent(article1_url, test_cache):
        add_to_cache(article1_url, test_cache)
        print(f"Added {article1_url}")
    else:
        print(f"{article1_url} was already sent.")

    if not is_article_sent(article2_url, test_cache):
        add_to_cache(article2_url, test_cache)
        print(f"Added {article2_url}")
    else:
        print(f"{article2_url} was already sent.")
    
    save_cache(test_cache, "test_cache.json")
    print(f"Cache after adds: {test_cache}")

    # Test cleaning (assuming some time has passed or by setting specific timestamps)
    # Create a dummy old entry
    old_article_url = "http://example.com/old_article"
    old_timestamp = (datetime.utcnow() - timedelta(hours=DEFAULT_EXPIRY_HOURS + 1)).isoformat()
    add_to_cache(old_article_url, test_cache, timestamp=old_timestamp)
    save_cache(test_cache, "test_cache.json")
    print(f"Cache before cleaning: {load_cache('test_cache.json')}")
    
    # Clean the cache
    pruned = clean_cache(test_cache, expiry_hours=DEFAULT_EXPIRY_HOURS) # Pass test_cache directly
    save_cache(test_cache, "test_cache.json") # Save the modified test_cache
    print(f"Pruned {pruned} articles.")
    print(f"Cache after cleaning: {load_cache('test_cache.json')}")

    # Clean up test file
    if os.path.exists("test_cache.json"):
        os.remove("test_cache.json")
