def detect_candle_patterns(df):
    df.loc[:, "Pattern"] = "None"  # Use .loc to avoid SettingWithCopyWarning

    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]

        # Hammer
        if (curr["close"] > curr["open"] and
            curr["low"] < curr["open"] and
            curr["low"] < curr["close"] and
            (curr["open"] - curr["low"]) > 2 * (curr["close"] - curr["open"])):
            df.at[df.index[i], "Pattern"] = "Hammer"

        # Doji
        elif abs(curr["close"] - curr["open"]) <= 0.1 * (curr["high"] - curr["low"]):
            df.at[df.index[i], "Pattern"] = "Doji"

        # Engulfing
        elif (curr["open"] < curr["close"] and
              prev["open"] > prev["close"] and
              curr["open"] < prev["close"] and
              curr["close"] > prev["open"]):
            df.at[df.index[i], "Pattern"] = "Bullish Engulfing"

        elif (curr["open"] > curr["close"] and
              prev["open"] < prev["close"] and
              curr["open"] > prev["close"] and
              curr["close"] < prev["open"]):
            df.at[df.index[i], "Pattern"] = "Bearish Engulfing"

    return df
