import logging

logging.basicConfig(
    filename="bot.log",  # Remove filename=... for console logs while debugging
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

import threading
import uvicorn
import asyncio
from api_receiver import app
from marketdata import get_ohlc
from botstrategies import analyze_symbol
from telegrambot import start_telegram_listener

# Analysis loop
async def run_analysis_loop():
    symbols = ["XAUUSD", "XAGUSD", "EURUSD", "US30M", "INDNASDAQ"]
    while True:
        try:
            logger.info("🔄 Running scheduled analysis...")
            for symbol in symbols:
                try:
                     df = await get_ohlc(symbol, "H1", bars=200)
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
    asyncio.run(run_analysis_loop())

def run_api():
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.exception("API server crashed: %s", e)

if __name__ == "__main__":
    # Start background threads FIRST
    t1 = threading.Thread(target=run_analysis, name="AnalysisThread", daemon=True)
    t2 = threading.Thread(target=run_api, name="ApiThread", daemon=True)
    t1.start()
    t2.start()
    # Telegram bot runs in main thread
    start_telegram_listener()
