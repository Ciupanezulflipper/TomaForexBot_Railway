# main_launcher.py

import asyncio
import logging
from datetime import datetime
from botstrategies import analyze_symbol
from marketdata import get_ohlc
from telegrambot import setup_telegram_bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYMBOLS = ["XAUUSD", "XAGUSD", "EURUSD", "US30", "NAS100"]

async def scheduled_analysis():
    logger.info("🔄 Running scheduled analysis...")
    for symbol in SYMBOLS:
        try:
            df = await get_ohlc(symbol, "H1", bars=200)
            if df.empty:
                logger.warning(f"❌ No data returned for {symbol}")
                continue

            signal = analyze_symbol(symbol, df)
            if signal:
                logger.info(f"📊 Signal for {symbol}: {signal}")
            else:
                logger.info(f"ℹ️ No strong signal for {symbol}")

        except Exception as e:
            logger.error(f"⚠️ Error analyzing {symbol}: {e}")
            continue
    logger.info("✅ Analysis complete. Waiting 15 minutes...")

async def main():
    await setup_telegram_bot()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_analysis, "interval", minutes=15)
    scheduler.start()

    # Run initial analysis once
    await scheduled_analysis()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
