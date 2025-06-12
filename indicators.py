# indicators.py

import pandas as pd
import os

print(f"[DEBUG] indicators.py loaded from {os.path.abspath(__file__)}")

def calculate_ema(series, period=9):
"""Return the Exponential Moving Average series."""
    print(f"[DEBUG] EMA input: {series.name}, length={len(series)}")
    ema_series = series.ewm(span=period, adjust=False).mean()
    return ema_series

def calculate_rsi(series, period=14):
 """Return the Relative Strength Index series."""
    print(f"[DEBUG] rsi input: {series.name}, length={len(series)}")
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
     return rsi
