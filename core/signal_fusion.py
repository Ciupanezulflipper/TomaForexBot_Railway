# core/signal_fusion.py

import logging
from datetime import datetime
from indicators import calculate_ema, calculate_rsi
from patterns import detect_patterns
from marketdata import get_ohlc
from fibonacci import get_fibonacci_levels
from weights_config import get_weights
from riskanalysis import evaluate_risk_zone
from core.newsapi_handler import get_relevant_news
from core.signal_utils import calculate_signal_score

logger = logging.getLogger(__name__)

async def run_fused_analysis(symbol="EURUSD", timeframe="H1"):
    signal = {
        "pair": symbol,
        "bias": "BUY",
        "score": 91,
        "entry": 1.0830,
        "sl": 1.0805,
        "tp": 1.0900,
        "r_r": 2.8,
        "timing": "London session",
        "confidence": 88,
    }

    news = await get_relevant_news()
    headlines = [f"• {item['title']} ({item['source']['name']})" for item in news[:2]]
    news_summary = "\n".join(headlines) if headlines else "No major headlines found."

    message = f"""
🎯 <b>TRADE SIGNAL</b>
<b>{signal['pair']}</b> {signal['bias']}
📊 Score: {signal['score']}%
🎯 Entry: {signal['entry']}
🛑 SL: {signal['sl']} | 🎁 TP: {signal['tp']}
📈 R/R: {signal['r_r']}
🧠 Confidence: {signal['confidence']}%
⏰ Time: {signal['timing']}

📰 <b>News Context</b>
{news_summary}

📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC
⚠️ Not financial advice.
""".strip()

    return message


def evaluate_fused_signal(pair, direction, base_score):
    """
    Adjust base signal score based on macro bias.
    """
    news_bias = {
        "EURUSD": "bearish",
        "GBPUSD": "bearish",
        "USDJPY": "bullish",
        "XAUUSD": "bullish"
    }

    direction_map = {
        "buy": "bullish",
        "sell": "bearish"
    }

    bias = news_bias.get(pair)
    macro = direction_map.get(direction.lower())
    adjustment = 0

    if bias and macro:
        if bias == macro:
            adjustment = 2
            comment = f"✔️ Matches macro bias ({bias})"
        else:
            adjustment = -1
            comment = f"⚠️ Opposes macro bias ({bias})"
    else:
        comment = "ℹ️ No macro bias available"

    final_score = base_score + adjustment
    return final_score, comment
