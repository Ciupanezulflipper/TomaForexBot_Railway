import pandas as pd

def calc_atr(df: pd.DataFrame, period: int = 14) -> float:
    """
    Calculate the Average True Range (ATR) from OHLCV data.
    """
    if df is None or df.empty or len(df) < period + 1:
        return 0.0

    high = df['high']
    low = df['low']
    close = df['close']

    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(window=period).mean()
    return round(atr.iloc[-1], 5) if not atr.empty else 0.0
