# core/signal_fusion.py

from datetime import datetime
from core.newsapi_handler import get_relevant_news

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
