"""
Main entry point for the bot.

Mode 1: Multi-process — Runs API, analysis, and Telegram bot in separate OS processes.
Mode 2: Asyncio-only — Runs all components as async coroutines in a single loop.

Switch modes with: BOT_MODE=multiprocess or BOT_MODE=asyncio
"""

import os
import sys
import logging
import signal

from config import SYMBOLS, ANALYSIS_INTERVAL_MINUTES, LOG_TO_CONSOLE, LOG_LEVEL

# ----- Setup Logging -----
def setup_logging():
    handlers = [logging.StreamHandler()] if LOG_TO_CONSOLE else [logging.FileHandler("bot.log")]
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True
    )
setup_logging()
logger = logging.getLogger(__name__)

# ==========================
# 🔹 MULTIPROCESS VERSION 🔹
# ==========================

def run_api_process():
    import uvicorn
    from api_receiver import app
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level=LOG_LEVEL.lower())
    except Exception:
        logger.exception("API server crashed")

def run_analysis_process():
    import asyncio
    from marketdata import get_ohlc
    from botstrategies import analyze_symbol

    async def analysis_loop():
        while True:
            logger.info("🔄 Running analysis...")
            for symbol in SYMBOLS:
                try:
                    df = await get_ohlc(symbol, "H1", bars=200)
                    if df is not None and not df.empty:
                        await analyze_symbol(df, symbol, "H1")
                        logger.info(f"✅ Done: {symbol}")
                    else:
                        logger.warning(f"❌ No data: {symbol}")
                except Exception as e:
                    logger.exception(f"⚠️ Analysis failed for {symbol}")
            logger.info(f"⏳ Sleeping {ANALYSIS_INTERVAL_MINUTES}min...")
            await asyncio.sleep(ANALYSIS_INTERVAL_MINUTES * 60)

    try:
        asyncio.run(analysis_loop())
    except Exception:
        logger.exception("Analysis process crashed")

def run_telegram_process():
    from telegrambot import start_telegram_listener
    try:
        start_telegram_listener()
    except Exception:
        logger.exception("Telegram bot crashed")

def run_multiprocess():
    import multiprocessing
    processes = []
    for fn in (run_api_process, run_analysis_process, run_telegram_process):
        p = multiprocessing.Process(target=fn)
        p.start()
        processes.append(p)

    def shutdown(signum, frame):
        logger.info("🛑 Shutdown signal received")
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    for p in processes:
        p.join()

# =======================
# 🔹 ASYNCIO VERSION 🔹
# =======================

async def analysis_task():
    from marketdata import get_ohlc
    from botstrategies import analyze_symbol
    while True:
        logger.info("🔄 Running analysis...")
        for symbol in SYMBOLS:
            try:
                df = await get_ohlc(symbol, "H1", bars=200)
                if df is not None and not df.empty:
                    await analyze_symbol(df, symbol, "H1")
                    logger.info(f"✅ Done: {symbol}")
                else:
                    logger.warning(f"❌ No data: {symbol}")
            except Exception:
                logger.exception(f"⚠️ Analysis failed: {symbol}")
        logger.info(f"⏳ Sleeping {ANALYSIS_INTERVAL_MINUTES}min...")
        await asyncio.sleep(ANALYSIS_INTERVAL_MINUTES * 60)

async def uvicorn_task():
    import uvicorn
    from api_receiver import app
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level=LOG_LEVEL.lower(), loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()

async def telegram_task():
    from telegrambot import start_telegram_listener_async
    await start_telegram_listener_async()  # You must implement this async function

async def run_asyncio_all():
    import asyncio

    stop_event = asyncio.Event()

    def handle_shutdown():
        logger.info("🛑 Shutdown signal received — stopping...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown)

    tasks = [
        asyncio.create_task(analysis_task(), name="analysis"),
        asyncio.create_task(uvicorn_task(), name="api"),
        asyncio.create_task(telegram_task(), name="telegram"),
    ]

    await stop_event.wait()
    logger.info("🧹 Cancelling tasks...")
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("✅ Clean exit")

# ====================
# 🔹 ENTRY POINT 🔹
# ====================

if __name__ == "__main__":
    mode = os.getenv("BOT_MODE", "multiprocess")
    if mode.lower() == "asyncio":
        import asyncio
        asyncio.run(run_asyncio_all())
    else:
        run_multiprocess()
