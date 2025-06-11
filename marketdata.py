import os
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from finnhub_data import get_finnhub_data

load_dotenv()

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
    "COFFEE": "KC=F",
}

TIMEFRAME_MAP = {
    "M1": "1m",
    "M5": "5m",
    "M15": "15m",
    "M30": "30m",
    "H1": "1h",
    "H4": "4h",
    "D1": "1d",
}

async def get_yf_data(symbol, timeframe="H1", bars=200):
    """Fetch OHLC data from Yahoo Finance."""
    yf_symbol = YAHOO_SYMBOLS.get(symbol, symbol)
    interval = TIMEFRAME_MAP.get(timeframe, timeframe)
    try:
        print(f"[Yahoo] Fetching data for {symbol} → {yf_symbol} ({interval})")
        df = yf.download(
            yf_symbol, period="60d", interval=interval, progress=False
        )

        if df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.columns = df.columns.str.lower()
        df.columns.name = None

        df = df[["open", "high", "low", "close", "volume"]]
        df = df.dropna().tail(bars)
        return df

    except Exception as e:
        print(f"[Yahoo] Error fetching {symbol}: {e}")
        return pd.DataFrame()

# Backwards compatibility
async def get_yahoo_data(symbol, bars, timeframe="H1"):
    return await get_yf_data(symbol, timeframe, bars)

async def get_market_data(symbol, timeframe="H1", bars=200, source="yfinance"):
    """General market data fetcher with pluggable source."""
    if source == "finnhub":
        return await get_finnhub_data(symbol, interval=timeframe, limit=bars)
    return await get_yf_data(symbol, timeframe, bars)

async def get_ohlc(symbol, timeframe="H1", bars=200):
    print(f"[OHLC] Start fetching {symbol} - {timeframe}")

    df = await get_finnhub_data(symbol, interval=timeframe, limit=bars)
    if not df.empty:
        print(f"[Finnhub] Success for {symbol}")
    else:
        print(f"[Finnhub] Failed. Falling back to Yahoo for {symbol}")
        df = await get_yf_data(symbol, timeframe, bars)

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
