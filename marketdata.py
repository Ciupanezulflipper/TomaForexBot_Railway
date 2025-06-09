# marketdata.py

import os
import pandas as pd
import yfinance as yf
import aiohttp
import asyncio
from dotenv import load_dotenv
from finnhub_data import get_finnhub_data

load_dotenv()

# === Yahoo fallback ===
async def get_yahoo_data(symbol, bars):
    map_yahoo = {
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

    yf_symbol = map_yahoo.get(symbol, symbol)
    try:
        print(f"🌐 Fetching Yahoo data for {symbol} → {yf_symbol}")
        async with aiohttp.ClientSession() as session:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}?range=30d&interval=1h"
            async with session.get(url) as resp:
                data = await resp.json()

        result = data.get("chart", {}).get("result")
        if not result:
            return pd.DataFrame()
        result = result[0]
        indicators = result.get("indicators", {}).get("quote", [{}])[0]
        timestamps = result.get("timestamp", [])
        df = pd.DataFrame({
            "time": pd.to_datetime(timestamps, unit="s"),
            "open": indicators.get("open"),
            "high": indicators.get("high"),
            "low": indicators.get("low"),
            "close": indicators.get("close"),
            "volume": indicators.get("volume"),
        }).set_index("time")

        # Flatten columns if needed
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(-1)

        print(f"✅ Yahoo raw data: {len(df)} rows")
        if df.empty:
            print(f"⚠️ Yahoo returned empty for {symbol}")
            return pd.DataFrame()

        df.rename(columns={
            "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Volume": "volume",
            "Adj Close": "adj_close"
        }, inplace=True)

        if 'adj_close' in df.columns:
            df.drop(columns=['adj_close'], inplace=True)

        # Ensure all needed columns
        cols_needed = ["open", "high", "low", "close", "volume"]
        for c in cols_needed:
            if c not in df.columns:
                df[c] = None
        return df[cols_needed].tail(bars)

    except Exception as e:
        print(f"❌ Yahoo error for {symbol}: {e}")
        return pd.DataFrame()

# === Unified fetch function ===
async def get_ohlc(symbol, timeframe="H1", bars=200):
    df = pd.DataFrame()

    # Try Finnhub
    print(f"⚠️ Trying Finnhub for {symbol}...")
    df = await get_finnhub_data(symbol, interval=timeframe, limit=bars)
    if not df.empty:
        print(f"✅ Finnhub data OK for {symbol}")

    # Try Yahoo if Finnhub fails
    if df.empty:
        print(f"⚠️ Trying Yahoo for {symbol}...")
        df = await get_yahoo_data(symbol, bars)
        if not df.empty:
            print(f"✅ Yahoo data OK for {symbol}")

    if df.empty:
        print(f"❌ All sources failed for {symbol}")
        return df

    df.columns = df.columns.str.lower()

    # === Calculate indicators ===
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
