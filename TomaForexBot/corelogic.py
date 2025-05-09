from indicators import calculate_ema, calculate_rsi
from patterns import detect_candle_patterns
from logger import log_to_csv
from fibonacci import calculate_fibonacci_levels, match_fibonacci_price

def analyze_symbol(symbol, df):
    df["ema9"] = calculate_ema(df["close"], period=9)
    df["ema21"] = calculate_ema(df["close"], period=21)
    df["rsi"] = calculate_rsi(df["close"], period=14)
    df["patterns"] = detect_candle_patterns(df)

    last_row = df.iloc[-1]

    score = 0
    reasons = []

    if last_row["ema9"] > last_row["ema21"]:
        score += 1
        reasons.append("EMA9 > EMA21")

    if last_row["rsi"] > 55:
        score += 1
        reasons.append("RSI > 55")

    if isinstance(last_row["patterns"], str) and last_row["patterns"]:
        score += 1
        reasons.append(f"Pattern: {last_row['patterns']}")

    fib = calculate_fibonacci_levels(df)
    matched_level = match_fibonacci_price(last_row["close"], fib)
    if matched_level:
        score += 1
        reasons.append(f"Fibonacci near {matched_level}")

    if score >= 3:
        signal = "BUY"
    elif score <= 1:
        signal = "SELL"
    else:
        signal = "WAIT"

    log_to_csv(symbol, signal, score, reasons)
    return {
        "symbol": symbol,
        "score": score,
        "signal": signal,
        "rsi": last_row["rsi"],
        "ema9": last_row["ema9"],
        "ema21": last_row["ema21"],
        "pattern": last_row["patterns"],
        "reasons": reasons,
        "timestamp": str(last_row.name)
    }
