from telegram import Update
from telegram.ext import ContextTypes

from marketdata import get_yf_data
from finnhub_data import get_finnhub_data

import asyncio

async def connect_finnhub():
    """Async ping for Finnhub."""
    try:
        df = await get_finnhub_data("AAPL", interval="H1", limit=5)
        return not df.empty
    except Exception as e:
        print(f"Finnhub connect error: {e}")
        return False

async def connect_yahoo():
    """Async ping for Yahoo."""
    try:
        df = await get_yf_data("AAPL", "H1", 5)
        return not df.empty
    except Exception as e:
        print(f"Yahoo connect error: {e}")
        return False

async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    finnhub_ok, yahoo_ok = await asyncio.gather(connect_finnhub(), connect_yahoo())

    status_lines = [
        f"Finnhub: {'🟢 Connected' if finnhub_ok else '❌ Not connected'}",
        f"Yahoo: {'🟢 Connected' if yahoo_ok else '❌ Not connected'}"
    ]
    overall = "✅ All data sources OK" if all([finnhub_ok, yahoo_ok]) else "⚠️ Some data sources failed"
    await update.message.reply_text('\n'.join(status_lines + [overall]))

def get_bot_status():
    return "Bot is running."
