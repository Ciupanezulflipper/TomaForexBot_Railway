# finnhub_news_fetcher.py (update with manual .env load)

import os
import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ✅ Manually load .env for standalone script testing
load_dotenv()
API_KEY = os.getenv("FINNHUB_API_KEY")

async def fetch_recent_forex_news(hours_ago: int = 6):
    if not API_KEY:
        print("[⚠️] FINNHUB_API_KEY not set — skipping news fetch.")
        return []

    try:
        url = f"https://finnhub.io/api/v1/news?category=forex&token={API_KEY}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

        cutoff = datetime.utcnow() - timedelta(hours=hours_ago)
        recent_news = [n for n in data if 'datetime' in n and datetime.utcfromtimestamp(n['datetime']) > cutoff]

        return recent_news[:5]

    except Exception as e:
        print(f"[ERROR] Failed to fetch news from Finnhub: {e}")
        return []

if __name__ == "__main__":
    import asyncio
    async def test():
        articles = await fetch_recent_forex_news()
        for a in articles:
            print(f"📰 {a.get('headline')}\n🔗 {a.get('url')}\n")
    asyncio.run(test())
