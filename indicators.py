"""Utility indicator calculations."""

from __future__ import annotations

import os
import pandas as pd

print(f"[DEBUG] indicators.py loaded from {os.path.abspath(__file__)}")


def calculate_ema(series: pd.Series, period: int = 9) -> pd.Series:
    """Return the Exponential Moving Average series."""
    print(f"[DEBUG] EMA input: {series.name}, length={len(series)}")
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Return the Relative Strength Index series."""
    print(f"[DEBUG] rsi input: {series.name}, length={len(series)}")
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(to_replace=0, method="ffill")
    rsi = 100 - (100 / (1 + rs))
    return rsi