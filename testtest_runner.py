import asyncio
from core.signal_fusion import get_combined_signal
from core.newsapi_handler import get_relevant_news
from core.csv_logger import log_news_alert, log_trade_signal

async def run_test():
    print("🔍 Testing trade signal...")
    signal_text = await get_combined_signal()
    print(signal_text)

    signal_mock = {
        "pair": "EUR/USD",
        "bias": "BUY",
        "score": 91,
        "entry": 1.0830,
        "sl": 1.0805,
        "tp": 1.0900,
        "r_r": 2.8,
        "timing": "London session",
        "confidence": 88,
    }
    log_trade_signal(signal_mock)

    print("\n📰 Testing news fetch...")
    news = await get_relevant_news()
    for i, article in enumerate(news[:3]):
        print(f"{i+1}. {article['title']} ({article['source']['name']})")
        log_news_alert(article)

if __name__ == "__main__":
    asyncio.run(run_test())
