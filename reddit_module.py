
 # reddit_module.py
 import praw
 import logging
 from datetime import datetime, timezone
 
 # ---- CONFIG: Fill in your Reddit API details ----
 REDDIT_CLIENT_ID = "lIRvK760FWnMY3qPYPBaww"
 REDDIT_CLIENT_SECRET = "J5bKYKVwdzPF9FywnuY38dMLFUl_cw"
 REDDIT_USER_AGENT = "TomaNewsBot/1.0 by u/CriticismVisual130"
 
 # Optional: Add specific subreddits to target
 SUBREDDITS = [
     "Forex",
     "StockMarket",
     "economy",
     "CryptoCurrency",
     "worldnews"
 ]
 
 # Max headlines per subreddit
 HEADLINE_LIMIT = 8
 
 # Set up logging for debugging
 logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
 logger = logging.getLogger(__name__)
 
 def get_reddit_headlines():
     """
     Fetches recent hot headlines from configured subreddits.
     Returns: List of (headline, subreddit, url, utc_timestamp)
     """
     reddit = praw.Reddit(
         client_id=CriticismVisual130,
         client_secret=bHXQaruV9oUv4i-NZ8XV3JDyKHRNwg,
