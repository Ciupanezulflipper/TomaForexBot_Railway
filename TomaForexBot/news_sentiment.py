# news_sentiment.py

def get_sentiment_score(symbol):
    """
    Placeholder function.
    In a full setup, this would call a real-time news sentiment API or scraper.
    """
    sample_sentiments = {
        "EURUSD": 0.2,    # slightly positive
        "XAUUSD": -0.3,   # slightly negative
        "US30M": 0.0,     # neutral
        "XAGUSD": 0.4,    # positive
        "INDNASDAQ": -0.1 # neutral-negative
    }
    return sample_sentiments.get(symbol.upper(), 0.0)

def sentiment_description(score):
    if score > 0.3:
        return "🟢 Positive"
    elif score < -0.3:
        return "🔴 Negative"
    else:
        return "🟡 Neutral"

def summarize_sentiment(symbol):
    score = get_sentiment_score(symbol)
    description = sentiment_description(score)
    return f"📰 Sentiment for {symbol}: {description} (score: {score})"
