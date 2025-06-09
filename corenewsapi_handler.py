import aiohttp
from datetime import datetime, timedelta
import os

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

NEWS_KEYWORDS = [
    "fed", "federal reserve", "interest rate", "inflation",
    "gdp", "employment", "bank of england", "ecb",
    "european central bank", "recession", "economic slowdown",
    "us treasury", "yield", "macroeconomics", "rate hike"
]

async def get_relevant_news():
    now = datetime.utcnow()
    since = (now - timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M:%S')

    url = "https://newsapi.org/v2/everything"
    params = {
        'apiKey': NEWS_API_KEY,
        'q': 'forex OR USD OR EUR OR GBP OR "central bank"',
        'language': 'en',
        'sortBy': 'publishedAt',
        'from': since,
        'pageSize': 20
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                articles = data.get('articles', [])
                filtered = []
                for article in articles:
                    text = (article.get("title", "") + article.get("description", "")).lower()
                    if any(keyword in text for keyword in NEWS_KEYWORDS):
                        filtered.append(article)
                return filtered
            return []
