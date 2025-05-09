import pandas as pd
from indicators import calculate_ema, calculate_rsi
from patterns import detect_candle_patterns
from logger import log_to_csv
from fibonacci import calculate_fibonacci_levels, match_fibonacci_price

def analyze_symbol(symbol, df):
    df["ema9"] = calculate_ema(df["close"], period=9)
    df["ema21"] = calculate_ema(df["close"], period=21)
    df["rsi"] = calculate_rsi(df["close"], period=14)

    patterns = detect_candle_patterns(df)
    df = pd.concat([df, patterns], axis=1)

    high_val = df["high"].max()
low_val = df["low"].min()

high_val = float(high_val.values[0]) if hasattr(high_val, "values") else float(high_val)
low_val = float(low_val.values[0]) if hasattr(low_val, "values") else float(low_val)

fib_levels = calculate_fibonacci_levels(high=high_val, low=low_val)
    )

    last_price = df["close"].iloc[-1]
    last_price = float(last_price.values[0]) if hasattr(last_price, "values") else float(last_price)

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
        signal["reasons"].append("EMA9 > EMA21")

    if latest["rsi"] < 30:
        signal["score"] += 1
        signal["reasons"].append("RSI oversold")
    elif latest["rsi"] > 70:
        signal["score"] -= 1
        signal["reasons"].append("RSI overbought")

    if signal["pattern"] != "None":
        signal["score"] += 1
        signal["reasons"].append(f"Pattern: {signal['pattern']}")

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
