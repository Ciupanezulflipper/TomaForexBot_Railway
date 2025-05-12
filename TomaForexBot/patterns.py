import pandas as pd

def detect_candle_patterns(df):
    df.loc[:, "Pattern"] = "None"

    for i in range(1, len(df)):
        try:
            prev = df.iloc[i - 1]
            curr = df.iloc[i]

            # ✅ Sanity check to skip rows with missing data
            if pd.isnull(curr[["open", "close", "high", "low"]]).any():
                continue
            if pd.isnull(prev[["open", "close"]]).any():
                continue

            # ✅ Safe single-value comparisons
            open_ = curr["open"]
            close = curr["close"]
            high = curr["high"]
            low = curr["low"]

            prev_open = prev["open"]
            prev_close = prev["close"]

            # Hammer
            if (
                close > open_ and
                (open_ - low) > 2 * (close - open_)
            ):
                df.at[df.index[i], "Pattern"] = "Hammer"

            # Doji
            elif abs(close - open_) <= 0.1 * (high - low):
                df.at[df.index[i], "Pattern"] = "Doji"

            # Bullish Engulfing
            elif (
                open_ < close and
                prev_open > prev_close and
                open_ < prev_close and
                close > prev_open
            ):
                df.at[df.index[i], "Pattern"] = "Bullish Engulfing"

            # Bearish Engulfing
            elif (
                open_ > close and
                prev_open < prev_close and
                open_ > prev_close and
                close < prev_open
            ):
                df.at[df.index[i], "Pattern"] = "Bearish Engulfing"

        except Exception as e:
            print(f"⚠️ Pattern error at row {i}: {e}")
            continue

    return df
