import asyncio
from datetime import datetime, timedelta
import logging

from newsbot import fetch_news, extract_asset, keyword_sentiment, get_atr, format_telegram_message, log_signal, send_telegram_message_sync
from news_memory import NewsMemory
from botstrategies import analyze_symbol_single

ASSETS = ["US30", "USDCHF", "USDJPY", "OIL"]
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def hybrid_check(asset, memory):
    news_items = await fetch_news(asset)
    for news in news_items:
        news_url = news.get('url')
        if not news_url or memory.already_sent(news_url):
            continue

        text = news['title'] + ". " + news.get('description', '')
        detected_asset = extract_asset(text)
        if not detected_asset:
            continue

        news_signal, bias = keyword_sentiment(text, detected_asset)
        if news_signal == "HOLD":
            continue

        # Technical confirmation
        tech_result = await analyze_symbol_single(detected_asset, "H1")
        if "❌" in tech_result:
            continue

        tech_signal = "BUY" if "Signal: BUY" in tech_result else "SELL"

        if news_signal == tech_signal:
            atr = get_atr(detected_asset)
            try:
                entry = float(tech_result.split("ema21: ")[-1].split("\n")[0])
            except:
                logger.warning(f"[ENTRY] Fallback to ATR for {detected_asset}")
                entry = atr * 10  # crude fallback estimate

            sl = round(entry - atr, 4) if tech_signal == "SELL" else round(entry + atr, 4)
            tp = round(entry - 2 * atr, 4) if tech_signal == "SELL" else round(entry + 2 * atr, 4)

            message = format_telegram_message(
                detected_asset, tech_signal, tech_result, sl, tp, news
            )
            send_telegram_message_sync(message)
            memory.remember_news(news_url)
            log_signal({
                "asset": detected_asset,
                "signal": tech_signal,
                "bias": bias,
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "timestamp": datetime.now().isoformat(),
                "news_url": news_url,
                "news_title": news['title']
            })
            logger.info(f"[Signal] {tech_signal} {detected_asset} confirmed by news + TA")
        else:
            logger.info(f"[Conflict] News says {news_signal}, TA says {tech_signal} for {detected_asset}")

async def hybrid_loop():
    memory = NewsMemory()
    while True:
        logger.info("[HybridBot] Checking all assets...")
        tasks = [hybrid_check(asset, memory) for asset in ASSETS]
        await asyncio.gather(*tasks)
        logger.info("[HybridBot] Sleeping for 15 minutes...")
        await asyncio.sleep(900)

if __name__ == "__main__":
    asyncio.run(hybrid_loop())
