"""
Market data utilities for fetching OHLCV and common indicators.
- Async, pandas DataFrame return.
- Handles multiple sources (Finnhub, Yahoo), fallback and error handling.
- Type annotations and docstrings.
- Uses logging module instead of print.
- Allows configurable lookback period and columns.
"""

import os
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from finnhub_data import get_finnhub_data
from typing import Optional, List, Dict, Any, Union
import logging

load_dotenv()
logger = logging.getLogger(__name__)

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

async def get_yf_data(
    symbol: str,
    timeframe: str = "H1",
    bars: int = 200,
    period: Optional[str] = None,
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance.

    Args:
        symbol (str): Ticker symbol (internal).
        timeframe (str): Standard timeframe key ("H1", "D1", etc).
        bars (int): Number of bars.
        period (str, optional): Yahoo period string (e.g. "60d"). If None, defaults to "60d".
        columns (list, optional): Columns to return, defaults to ["open","high","low","close","volume"].

    Returns:
        pd.DataFrame: DataFrame with requested columns, sorted by date ascending.
    """
    yf_symbol = YAHOO_SYMBOLS.get(symbol, symbol)
    interval = TIMEFRAME_MAP.get(timeframe, timeframe)
    if period is None:
        period = "60d"
    if columns is None:
        columns = ["open", "high", "low", "close", "volume"]
    try:
        logger.info(f"[Yahoo] Fetching data for {symbol} → {yf_symbol} ({interval}, period={period})")
        df = yf.download(
            yf_symbol, period=period, interval=interval, progress=False
        )
        if df.empty:
            logger.warning(f"[Yahoo] No data for {symbol}")
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = df.columns.str.lower()
        df.columns.name = None
        # Only keep the requested columns if present
        available_cols = [c for c in columns if c in df.columns]
        df = df[available_cols].dropna().tail(bars)
        df = df.sort_index()
        return df
    except Exception as e:
        logger.error(f"[Yahoo] Error fetching {symbol}: {e}")
        return pd.DataFrame()

# Backwards compatibility alias
async def get_yahoo_data(
    symbol: str, bars: int, timeframe: str = "H1"
) -> pd.DataFrame:
    return await get_yf_data(symbol, timeframe, bars)

async def get_market_data(
    symbol: str,
    timeframe: str = "H1",
    bars: int = 200,
    source: str = "yfinance",
    period: Optional[str] = None,
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    General market data fetcher with pluggable source.

    Args:
        symbol (str): Ticker.
        timeframe (str): Timeframe key.
        bars (int): Number of bars.
        source (str): Data source ("finnhub" or "yfinance").
        period (str, optional): Period string for Yahoo.
        columns (list, optional): Columns to keep.

    Returns:
        pd.DataFrame: DataFrame with requested columns.
    """
    if source == "finnhub":
        # Finnhub does not support custom columns or period
        return await get_finnhub_data(symbol, interval=timeframe, limit=bars)
    return await get_yf_data(symbol, timeframe, bars, period=period, columns=columns)

async def get_ohlc(
    symbol: str,
    timeframe: str = "H1",
    bars: int = 200,
    columns: Optional[List[str]] = None,
    period: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch OHLCV data for a symbol, with fallback from Finnhub to Yahoo Finance.

    Args:
        symbol (str): Symbol to fetch.
        timeframe (str): Timeframe key.
        bars (int): Number of bars.
        columns (list, optional): Columns to keep.
        period (str, optional): Yahoo period string.

    Returns:
        pd.DataFrame: DataFrame with at least 'open','high','low','close','volume' columns.
    """
    logger.info(f"[OHLC] Start fetching {symbol} - {timeframe}")
    df = await get_finnhub_data(symbol, interval=timeframe, limit=bars)
    if not df.empty:
        logger.info(f"[Finnhub] Success for {symbol}")
    else:
        logger.warning(f"[Finnhub] Failed. Falling back to Yahoo for {symbol}")
        df = await get_yf_data(symbol, timeframe, bars, period=period, columns=columns)
    if df.empty:
        logger.error(f"[ERROR] No data available for {symbol}")
        return df
    df.columns = df.columns.str.lower()
    # Add indicators if "close" is present
    if "close" in df.columns:
        if "ema9" not in df.columns:
            df["ema9"] = df["close"].ewm(span=9, adjust=False).mean()
        if "ema21" not in df.columns:
            df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()
        if "rsi" not in df.columns:
            delta = df["close"].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df["rsi"] = 100 - (100 / (1 + rs))
    # Only keep requested columns if specified
    if columns is not None:
        available_cols = [c for c in columns if c in df.columns]
        df = df[available_cols]
    return df

def set_logging_level(level: Union[int, str] = logging.INFO):
    """
    Utility to set the logging level for this module.
    """
    logging.basicConfig(level=level)
