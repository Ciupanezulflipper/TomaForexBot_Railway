# marketdata.py

import os
import pandas as pd
import yfinance as yf
import aiohttp
import asyncio
from dotenv import load_dotenv
from finnhub_data import get_finnhub_data

load_dotenv()

# Yahoo symbol map
YAHOO_SYMBOLS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "USDCHF": "CHF=X",
    "AUDUSD": "AUDUSD=X",
    "NZDUSD": "NZDUSD=X",
    "USDCAD": "CAD=X",
    "XAUUSD": "GC=F",
    "XAGUSD": "SI=F",
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "US30": "^DJI",
    "NAS100": "^IXIC",
    "SPX500": "^GSPC",
    "WTI": "CL=F",
    "NGAS": "NG=F",
    "COFFEE": "KC=F"
}

async def get_yahoo_data(symbol, bars):
    yf_symbol = YAHOO_SYMBOLS.get(symbol, symbol)
    try:
        print(f"[Yahoo] Fetching data for {symbol} → {yf_symbol}")
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}?range=30d&interval=1h"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

        chart_data = data.get("chart", {}).get("result", [{}])[0]
        timestamps = chart_data.get("timestamp", [])
        quotes = chart_data.get("indicators", {}).get("quote", [{}])[0]

        if not timestamps or not quotes:
            return pd.DataFrame()

        df = pd.DataFrame({
            "time": pd.to_datetime(timestamps, unit="s"),
            "open": quotes.get("open"),
            "high": quotes.get("high"),
            "low": quotes.get("low"),
            "close": quotes.get("close"),
            "volume": quotes.get("volume"),
        }).set_index("time")

        df = df.dropna().tail(bars)
        return df

    except Exception as e:
        print(f"[Yahoo] Error fetching {symbol}: {e}")
        return pd.DataFrame()

async def get_ohlc(symbol, timeframe="H1", bars=200):
    print(f"[OHLC] Start fetching {symbol} - {timeframe}")

    df = await get_finnhub_data(symbol, interval=timeframe, limit=bars)
    if not df.empty:
        print(f"[Finnhub] Success for {symbol}")
    else:
        print(f"[Finnhub] Failed. Falling back to Yahoo for {symbol}")
        df = await get_yahoo_data(symbol, bars)

    if df.empty:
        print(f"[ERROR] No data available for {symbol}")
        return df

    df.columns = df.columns.str.lower()

    if "close" in df.columns:
        df["ema9"] = df["close"].ewm(span=9, adjust=False).mean()
        df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()

        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))

    return df
