# news_fetcher.py

import os
import aiohttp
import asyncpraw
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "TomaForexBot/1.0")

SUBREDDITS = ["Forex", "StockMarket", "WallStreetBets"]

async def fetch_newsapi_headlines(limit: int = 5):
    if not NEWS_API_KEY:
        return []
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": NEWS_API_KEY,
        "category": "business",
        "language": "en",
        "pageSize": limit,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                data = await resp.json()
                return [a.get("title", "") for a in data.get("articles", [])]
    except Exception:
        return []

async def fetch_reddit_headlines(limit: int = 5):
    if not (REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET):
        return []
    headlines = []
    reddit = asyncpraw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )
    try:
        for sub in SUBREDDITS:
            subreddit = await reddit.subreddit(sub)
            async for post in subreddit.hot(limit=limit):
                if getattr(post, "stickied", False):
                    continue
                headlines.append(post.title)
    except Exception:
        pass
    await reddit.close()
    return headlines[:limit]

async def fetch_combined_news():
    newsapi = await fetch_newsapi_headlines()
    reddit = await fetch_reddit_headlines()
    return newsapi + reddit
