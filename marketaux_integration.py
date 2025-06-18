import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
MARKETAUX_API_KEY = os.getenv('MARKETAUX_API_KEY')

def fetch_marketaux_news(symbol, limit=5):
    logger = logging.getLogger(__name__)
    url = f"https://api.marketaux.com/v1/news/all"
    params = {
        "api_token": MARKETAUX_API_KEY,
        "symbols": symbol,
        "limit": limit,
        "language": "en"
    }
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        news = r.json().get("data", [])
        logger.info(f"Fetched {len(news)} news for {symbol}")
        return [f"{item['published_at']} - {item['title']}" for item in news]
    except Exception as e:
        logger.error(f"Marketaux news fetch failed: {e}")
        return []