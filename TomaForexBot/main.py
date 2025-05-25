# TomaForexBot/main.py

import logging

logging.basicConfig(
    filename="bot.log",  # Log to file. Remove filename=... to log to console.
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

import threading
import uvicorn
import asyncio
import nest_asyncio
import time
from api_receiver import app
from marketdata import get_mt5_data
from botstrategies import analyze_symbol
from telegrambot import start_telegram_listener

nest_asyncio.apply()

def run_telegram():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_telegram_listener())
    except Exception as e:
        logger.exception("Telegram bot crashed: %s", e)

async def run_analysis_loop():
    symbols = ["XAUUSD", "XAGUSD", "EURUSD", "US30M", "INDNASDAQ"]
    while True:
        try:
            logger.info("🔄 Running scheduled analysis...")
            for symbol in symbols:
                try:
                    df = get_mt5_data(symbol, "H1", bars=200)
                    if df is not None and not df.empty:
                        await analyze_symbol(df, symbol, "H1")
                        logger.info(f"✅ Finished analysis for {symbol}")
                    else:
                        logger.warning(f"❌ No data returned for {symbol}")
                except Exception as e:
                    logger.error(f"⚠️ Error analyzing {symbol}: {e}")
            logger.info("✅ Analysis complete. Waiting 15 minutes...")
        except Exception as e:
            logger.exception(f"Critical error in scheduled analysis: {e}")
        await asyncio.sleep(900)  # 15 minutes

def run_analysis():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_analysis_loop())
    except Exception as e:
        logger.exception("Analysis thread crashed: %s", e)

def run_api():
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.exception("API server crashed: %s", e)

if __name__ == "__main__":
    t1 = threading.Thread(target=run_telegram, name="TelegramThread")
    t2 = threading.Thread(target=run_analysis, name="AnalysisThread")

    t1.start()
    t2.start()

    run_api()
