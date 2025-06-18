# finnhub_data.py
# Async OHLC fetcher using Finnhub API for Forex, indices, metals

import os
import aiohttp
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load .env for API key
load_dotenv()

# Get API key from environment
def get_api_key():
    key = os.getenv("FINNHUB_API_KEY")
    if not key:
        print("[⚠️] FINNHUB_API_KEY not set — skipping Finnhub requests.")
    return key

# Async OHLC fetcher
async def get_finnhub_data(symbol="EURUSD", interval="H1", limit=150):
    """
    Fetch OHLC data from Finnhub for supported symbols and intervals.
    Returns: DataFrame with datetime index and OHLCV columns.
    """
    api_key = get_api_key()
    if not api_key:
        return pd.DataFrame()

    base_url = "https://finnhub.io/api/v1/forex/candle"

    symbol_map = {
        "EURUSD": "OANDA:EUR_USD",
        "GBPUSD": "OANDA:GBP_USD",
        "USDJPY": "OANDA:USD_JPY",
        "USDCHF": "OANDA:USD_CHF",
        "AUDUSD": "OANDA:AUD_USD",
        "NZDUSD": "OANDA:NZD_USD",
        "USDCAD": "OANDA:USD_CAD",
        "XAUUSD": "OANDA:XAU_USD",
        "XAGUSD": "OANDA:XAG_USD",
        "US30": "FOREXCOM:DJI",
        "NAS100": "FOREXCOM:NSX",
        "SPX500": "FOREXCOM:SPX",
    }

    mapped_symbol = symbol_map.get(symbol.upper())
    if not mapped_symbol:
        print(f"⚠️ Finnhub: Symbol {symbol} not supported.")
        return pd.DataFrame()

    resolution_map = {
        "M1": "1", "M5": "5", "M15": "15", "M30": "30",
        "H1": "60", "H4": "240", "D1": "D"
    }

    resolution = resolution_map.get(interval.upper(), "60")
    now = int(datetime.utcnow().timestamp())
    past = now - limit * 3600  # ~1h bars

    url = (
        f"{base_url}?symbol={mapped_symbol}&resolution={resolution}"
        f"&from={past}&to={now}&token={api_key}"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                data = await res.json()

        if "c" not in data or not data["c"]:
            print(f"⚠️ No data from Finnhub for {symbol}")
            return pd.DataFrame()

        df = pd.DataFrame({
            "time": pd.to_datetime(data["t"], unit="s"),
            "open": data["o"],
            "high": data["h"],
            "low": data["l"],
            "close": data["c"],
            "volume": data["v"]
        }).set_index("time")

        return df

    except Exception as e:
        print(f"❌ Finnhub error: {e}")
        return pd.DataFrame()

# Optional: Visual score bar helper (for sentiment or strength visualization)
def score_bar(score):
    units = min(abs(score), 5)
    blocks = "█" * units
    return f"{blocks}{'🔺' if score > 0 else '🔻'}" if score != 0 else "—"
