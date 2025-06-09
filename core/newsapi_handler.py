import requests
import os
import aiohttp
from datetime import datetime, timedelta

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_news_sentiment(symbol):
    if not NEWS_API_KEY:
        return {"confidence": 0, "match": False, "reason": "Missing API key"}

    now = datetime.utcnow()
    since = (now - timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%S')

    query_map = {
        "EURUSD": "euro OR eurusd OR european central bank OR ECB",
        "GBPUSD": "pound OR gbpusd OR bank of england OR BOE",
        "USDJPY": "usd OR dollar OR fed OR FOMC",
        "XAUUSD": "gold OR XAUUSD OR precious metals"
    }

    query = query_map.get(symbol.upper(), f"{symbol} forex")

    url = "https://newsapi.org/v2/everything"
    params = {
        "apiKey": NEWS_API_KEY,
        "q": query,
        "from": since,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 10
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        articles = response.json().get("articles", [])
    except Exception as e:
        return {"confidence": 0, "match": False, "reason": str(e)}

    positive_keywords = ["rises", "bullish", "strength", "uptrend"]
    negative_keywords = ["falls", "bearish", "weakness", "downtrend"]

    score = 0
    for article in articles:
        content = f"{article.get('title', '')} {article.get('description', '')}".lower()
        if any(k in content for k in positive_keywords):
            score += 1
        if any(k in content for k in negative_keywords):
            score -= 1

    confidence = int((abs(score) / max(len(articles), 1)) * 100)
    match = score < 0 if "SELL" in symbol.upper() else score > 0

    return {
        "confidence": confidence,
        "match": match,
        "articles": len(articles),
        "score": score
    }

# ✅ Required by signal_fusion.py and other modules
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
                return data.get('articles', [])
            return []
