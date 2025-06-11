# scanner_loop.py

import asyncio
import logging
import os
from dotenv import load_dotenv
from news_signal_logic import fetch_and_analyze_news
from telegramsender import send_telegram_message
from core.signal_fusion import generate_trade_decision 

# --- CONFIG ---
SYMBOLS = ["EURUSD", "USDJPY", "XAUUSD", "US30"]
SCAN_INTERVAL_MINUTES = 30

load_dotenv()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

async def run_scan():
    for symbol in SYMBOLS:
        logging.info(f"Scanning {symbol}...")
        try:
            msg = await generate_trade_decision(symbol)
            if "BUY" in msg or "SELL" in msg:
                await send_telegram_message(msg, chat_id=TELEGRAM_CHAT_ID)
            else:
                logging.info(f"No signal for {symbol}")
        except Exception as e:
            logging.error(f"Error scanning {symbol}: {e}")

    logging.info("Scanning news only (no specific symbol)...")
    try:
        news_results = await fetch_and_analyze_news()
        if news_results:
            for h, sigs in news_results:
                lines = [f"📰 {h}"] + [f" - {s['pair']}: {s['signal']} ({s['reason']})" for s in sigs]
                await send_telegram_message("\n".join(lines), chat_id=TELEGRAM_CHAT_ID)
        else:
            logging.info("No actionable news found.")
    except Exception as e:
        logging.error(f"Error during news scan: {e}")

async def loop_scanner():
    while True:
        logging.info("Starting full scan cycle")
        await run_scan()
        logging.info(f"Sleeping for {SCAN_INTERVAL_MINUTES} minutes")
        await asyncio.sleep(SCAN_INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    try:
        asyncio.run(loop_scanner())
    except KeyboardInterrupt:
        logging.info("Stopped by user")
