import os
import logging
import praw
from dotenv import load_dotenv

load_dotenv()
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')
REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')  # Add this to your .env
REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')  # Add this to your .env

def post_reddit_alert(symbol, signal, reasons, subreddit="test"):
    logger = logging.getLogger(__name__)
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD
    )
    title = f"Trade Alert: {signal} {symbol}"
    body = f"Signal: {signal}\nSymbol: {symbol}\nReasons: {reasons}"
    try:
        submission = reddit.subreddit(subreddit).submit(title, selftext=body)
        logger.info(f"Posted Reddit alert to r/{subreddit}: {submission.url}")
    except Exception as e:
        logger.error(f"Reddit posting failed: {e}")