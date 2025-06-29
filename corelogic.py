import pandas as pd
from indicators import calculate_ema, calculate_rsi
from patterns import detect_candle_patterns
from logger import log_to_csv
from fibonacci import calculate_fibonacci_levels, match_fibonacci_price

def analyze_symbol(symbol, df):
    df["ema9"] = calculate_ema(df["close"], period=9)
    df["ema21"] = calculate_ema(df["close"], period=21)
    df["rsi"] = calculate_rsi(df["close"], period=14)

    df = detect_candle_patterns(df)

    # ✅ clean float values
    high_val = float(df["high"].values[-200:].max())
    low_val = float(df["low"].values[-200:].min())
    last_price = float(df["close"].iloc[-1])

    fib_levels = calculate_fibonacci_levels(high=high_val, low=low_val)
    fib_match = match_fibonacci_price(last_price, fib_levels)

    latest = df.iloc[-1]
    signal = {
        "symbol": symbol,
        "timeframe": "H1",
        "timestamp": latest.name.strftime("%Y-%m-%d %H:%M"),
        "ema9": latest["ema9"],
        "ema21": latest["ema21"],
        "rsi": latest["rsi"],
        "pattern": latest.get("pattern", "None"),
        "score": 0,
        "reasons": []
    }

    if latest["ema9"] > latest["ema21"]:
        signal["score"] += 1
        signal["reasons"].append("ema9 > ema21")

    if latest["rsi"] < 30:
        signal["score"] += 1
        signal["reasons"].append("rsi oversold")
    elif latest["rsi"] > 70:
        signal["score"] -= 1
        signal["reasons"].append("rsi overbought")

    if signal["pattern"] != "None":
        signal["score"] += 1
        signal["reasons"].append(f"pattern: {signal['pattern']}")

    if fib_match:
        signal["score"] += 1
        signal["reasons"].append(f"Price at Fib Level: {fib_match}")

    if signal["score"] >= 3:
        signal["signal"] = "BUY"
    elif signal["score"] <= -2:
        signal["signal"] = "SELL"
    else:
        signal["signal"] = "NEUTRAL"

    log_to_csv(signal)
    return signal
