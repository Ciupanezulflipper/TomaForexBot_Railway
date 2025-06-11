# news_signal_logic.py

import re
from news_fetcher import fetch_combined_news

# Simple scoring dictionary — expand this based on your use case
NEWS_KEYWORDS = {
    "interest rate hike": -1,
    "rate hike": -1,
    "inflation rising": -1,
    "tariff delay": +1,
    "stimulus package": +1,
    "strong gdp": +1,
    "bank failure": -1,
    "unemployment high": -1,
    "central bank support": +1,
    "usd weakness": +1,
    "usd strength": -1
}

def clean_text(text):
    return re.sub(r'[^\w\s]', '', text.lower())

def analyze_news_headline(headline, symbol="EURUSD"):
    """
    Returns a dict with score and reasons for one headline.
    """
    score = 0
    reasons = []
    text = clean_text(headline)

    for keyword, impact in NEWS_KEYWORDS.items():
        if keyword in text:
            score += impact
            reasons.append(f"{'🔺' if impact > 0 else '🔻'} {keyword}")

    result = {
        "symbol": symbol,
        "score": score,
        "reasons": reasons
    }
    return result

def analyze_multiple_headlines(headlines, symbol="EURUSD"):
    """
    Takes a list of headlines and returns cumulative score + reasons.
    """
    total_score = 0
    all_reasons = []

    for headline in headlines:
        res = analyze_news_headline(headline, symbol)
        total_score += res["score"]
        all_reasons.extend(res["reasons"])

    return {
        "symbol": symbol,
        "score": total_score,
        "reasons": all_reasons
    }

async def fetch_and_analyze_news():
    """Fetch headlines from multiple sources and analyze them."""
    headlines = await fetch_combined_news()
    results = []
    for h in headlines:
        sigs = analyze_news_headline(h)
        if sigs:
            results.append((h, sigs))
    return results
