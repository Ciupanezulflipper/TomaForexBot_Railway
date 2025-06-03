# news_signal_logic.py

# Maps for asset logic and keywords. Expand as needed.
ASSET_KEYWORDS = {
    "US30": ["dow", "us30", "djia", "wall street", "dow jones"],
    "EURUSD": ["eurusd", "euro", "eur", "ecb", "germany", "france", "italy"],
    "GBPUSD": ["gbpusd", "pound", "sterling", "boe", "uk", "england"],
    "USDJPY": ["usdjpy", "yen", "boj", "japan"],
    "XAUUSD": ["gold", "xau", "precious metal"],
    "OIL": ["oil", "brent", "wti", "crude"],
    # Add more as you want
}

BULLISH_WORDS = [
    "delay", "stimulus", "cut", "increase", "expand", "beat", "boost", "support", "approve",
    "positive", "growth", "record high", "record low unemployment", "risk-on"
]
BEARISH_WORDS = [
    "tariff", "ban", "sanction", "hike", "inflation", "reduce", "recession", "decline", "miss",
    "negative", "risk-off", "crash", "crisis", "lawsuit", "conflict"
]

# Asset reaction logic: asset, bull=buy/sell, bear=buy/sell
ASSET_IMPACT = {
    "US30": {"bull": "BUY", "bear": "SELL"},
    "EURUSD": {"bull": "BUY", "bear": "SELL"},
    "GBPUSD": {"bull": "BUY", "bear": "SELL"},
    "USDJPY": {"bull": "SELL", "bear": "BUY"},  # USD down, JPY up (risk-off)
    "XAUUSD": {"bull": "SELL", "bear": "BUY"},  # Risk-off: gold up
    "OIL": {"bull": "BUY", "bear": "SELL"},
    # Add more if needed
}

def analyze_news_headline(headline: str):
    headline_lower = headline.lower()
    results = []
    for asset, keywords in ASSET_KEYWORDS.items():
        for kw in keywords:
            if kw in headline_lower:
                score = 0
                for bull in BULLISH_WORDS:
                    if bull in headline_lower:
                        score += 1
                for bear in BEARISH_WORDS:
                    if bear in headline_lower:
                        score -= 1

                if score > 0:
                    signal = ASSET_IMPACT.get(asset, {}).get("bull", "NEUTRAL")
                elif score < 0:
                    signal = ASSET_IMPACT.get(asset, {}).get("bear", "NEUTRAL")
                else:
                    signal = "NEUTRAL"
                # Format result
                results.append({
                    "asset": asset,
                    "signal": signal,
                    "score": score,
                    "headline": headline,
                    "reason": f"Keyword: {kw}, Score: {score}"
                })
    # No asset matched, try general risk-on/off logic
    if not results:
        score = 0
        for bull in BULLISH_WORDS:
            if bull in headline_lower:
                score += 1
        for bear in BEARISH_WORDS:
            if bear in headline_lower:
                score -= 1
        if score > 0:
            general = "RISK-ON"
        elif score < 0:
            general = "RISK-OFF"
        else:
            general = "NEUTRAL"
        results.append({
            "asset": "GENERAL",
            "signal": general,
            "score": score,
            "headline": headline,
            "reason": f"General score: {score}"
        })
    return results

# Example: quick test
if __name__ == "__main__":
    test_headlines = [
        "Trump delays tariffs on Europe until July 9.",
        "ECB raises rates, inflation risk high.",
        "US jobless claims hit record low, Dow rallies.",
        "OPEC cuts crude production amid rising demand.",
        "Fed hikes rates, markets tumble."
    ]
    for h in test_headlines:
        out = analyze_news_headline(h)
        print(f"\nNEWS: {h}\nRESULT: {out}")
