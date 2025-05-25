import pandas as pd

def detect_candle_patterns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        df["Pattern"] = ""
        return df

    patterns_list = []
    for i in range(len(df)):
        row = df.iloc[:i+1]  # up to this candle (so prev and prev2 are available)
        patterns = []

        if i < 1:
            patterns_list.append("")
            continue

        last = row.iloc[-1]
        prev = row.iloc[-2]
        prev2 = row.iloc[-3] if i >= 2 else None

        last_open, last_close = last["open"], last["close"]
        last_high, last_low = last["high"], last["low"]
        last_bullish = last_close > last_open
        last_bearish = last_close < last_open

        body = abs(last_close - last_open)
        range_ = last_high - last_low
        upper_wick = last_high - max(last_close, last_open)
        lower_wick = min(last_close, last_open) - last_low

        if abs(last_close - last_open) < 0.1 * range_:
            patterns.append("Doji")
        if body < 0.3 * range_ and lower_wick > 2 * body and upper_wick < 0.3 * body:
            patterns.append("Hammer")
        if body < 0.3 * range_ and upper_wick > 2 * body and lower_wick < 0.3 * body:
            patterns.append("Inverted Hammer")

        if prev is not None:
            prev_open, prev_close = prev["open"], prev["close"]
            prev_bullish = prev_close > prev_open
            prev_bearish = prev_close < prev_open

            if last_bullish and prev_bearish and last_open <= prev_close and last_close >= prev_open:
                patterns.append("Bullish Engulfing")
            if last_bearish and prev_bullish and last_open >= prev_close and last_close <= prev_open:
                patterns.append("Bearish Engulfing")
            if prev_bearish and last_bullish and last_open >= prev_close and last_close <= prev_open:
                patterns.append("Bullish Harami")
            if prev_bullish and last_bearish and last_open <= prev_close and last_close >= prev_open:
                patterns.append("Bearish Harami")

        if prev2 is not None and prev is not None:
            prev2_open, prev2_close = prev2["open"], prev2["close"]
            prev2_bullish = prev2_close > prev2_open
            prev2_bearish = prev2_close < prev2_open

            if prev2_bearish and last_bullish:
                mid_body = abs(prev["close"] - prev["open"])
                if mid_body < 0.5 * abs(prev2_close - prev2_open) and last_close > ((prev2_open + prev2_close) / 2):
                    patterns.append("Morning Star")
            if prev2_bullish and last_bearish:
                mid_body = abs(prev["close"] - prev["open"])
                if mid_body < 0.5 * abs(prev2_close - prev2_open) and last_close < ((prev2_open + prev2_close) / 2):
                    patterns.append("Evening Star")

            if prev2_bullish and prev_bullish and last_bullish:
                patterns.append("Three White Soldiers")
            if prev2_bearish and prev_bearish and last_bearish:
                patterns.append("Three Black Crows")

        # Store patterns as comma-separated string
        patterns_list.append(", ".join(patterns) if patterns else "")

    df = df.copy()
    df["Pattern"] = patterns_list
    return df
