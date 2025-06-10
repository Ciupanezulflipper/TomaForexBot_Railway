# patterns.py
import pandas as pd

def detect_bullish_engulfing(df):
    if len(df) < 2:
        return False
    current = df.iloc[-1]
    previous = df.iloc[-2]
    return (
        previous['open'] > previous['close'] and
        current['close'] > current['open'] and
        current['open'] < previous['close'] and
        current['close'] > previous['open']
    )

def detect_bearish_engulfing(df):
    if len(df) < 2:
        return False
    current = df.iloc[-1]
    previous = df.iloc[-2]
    return (
        previous['close'] > previous['open'] and
        current['open'] > current['close'] and
        current['open'] > previous['close'] and
        current['close'] < previous['open']
    )

def detect_pin_bar(df, threshold=0.66):
    if len(df) < 1:
        return False
    c = df.iloc[-1]
    body = abs(c['close'] - c['open'])
    upper_shadow = c['high'] - max(c['close'], c['open'])
    lower_shadow = min(c['close'], c['open']) - c['low']
    total_range = c['high'] - c['low']
    if lower_shadow > threshold * total_range and body < 0.33 * total_range:
        return 'bullish'
    if upper_shadow > threshold * total_range and body < 0.33 * total_range:
        return 'bearish'
    return False

def detect_patterns(df):
    results = {}
    results['bullish_engulfing'] = detect_bullish_engulfing(df)
    results['bearish_engulfing'] = detect_bearish_engulfing(df)
    results['pin_bar'] = detect_pin_bar(df)
    return results

def detect_candle_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'pattern' column with simple candle pattern detection."""
    patterns = []
    for i in range(len(df)):
        sub = df.iloc[: i + 1]
        label = None
        if detect_bullish_engulfing(sub):
            label = "Bullish Engulfing"
        elif detect_bearish_engulfing(sub):
            label = "Bearish Engulfing"
        else:
            pin = detect_pin_bar(sub)
            if pin:
                label = f"{pin} pin bar"
        patterns.append(label or "None")

    df = df.copy()
    df["pattern"] = patterns
    return df
