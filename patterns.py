# patterns.py
import pandas as pd

def detect_bullish_engulfing(df):
    if len(df) < 2:
        return False
    current = df.iloc[-1]
    previous = df.iloc[-2]
    return (
        previous['Open'] > previous['Close'] and
        current['Close'] > current['Open'] and
        current['Open'] < previous['Close'] and
        current['Close'] > previous['Open']
    )

def detect_bearish_engulfing(df):
    if len(df) < 2:
        return False
    current = df.iloc[-1]
    previous = df.iloc[-2]
    return (
        previous['Close'] > previous['Open'] and
        current['Open'] > current['Close'] and
        current['Open'] > previous['Close'] and
        current['Close'] < previous['Open']
    )

def detect_pin_bar(df, threshold=0.66):
    if len(df) < 1:
        return False
    c = df.iloc[-1]
    body = abs(c['Close'] - c['Open'])
    upper_shadow = c['High'] - max(c['Close'], c['Open'])
    lower_shadow = min(c['Close'], c['Open']) - c['Low']
    total_range = c['High'] - c['Low']
    # Bullish pin bar: long lower shadow
    if lower_shadow > threshold * total_range and body < 0.33 * total_range:
        return 'bullish'
    # Bearish pin bar: long upper shadow
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