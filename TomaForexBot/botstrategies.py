import pandas as pd
from indicators import calculate_ema, calculate_rsi
from patterns import detect_candle_patterns
from fibonacci import calculate_fibonacci_levels, match_fibonacci_price
from logger import log_to_csv
from charting import generate_pro_chart
from telegrambot import send_telegram_message, send_telegram_photo

async def analyze_symbol(df, symbol, timeframe="H1", chat_id=None):
    if df is None or df.empty:
        return []

    df = calculate_ema(df)
    df = calculate_rsi(df)
    df = detect_candle_patterns(df)

    last = df.iloc[-1]
    score = 0
    reasons = []

    if last["EMA9"] > last["EMA21"]:
        score += 1
        reasons.append("EMA9 > EMA21")
    elif last["EMA9"] < last["EMA21"]:
        score += 1
        reasons.append("EMA9 < EMA21")

    if last["RSI"] < 30:
        score += 1
        reasons.append("RSI oversold")
    elif last["RSI"] > 70:
        score += 1
        reasons.append("RSI overbought")
    else:
        reasons.append("RSI neutral")

    fib_levels = calculate_fibonacci_levels(high=df["high"].max(), low=df["low"].min())
    fib_match = match_fibonacci_price(last["close"], fib_levels)
    if fib_match:
        score += 1
        reasons.append(f"near {fib_match} Fib level")

    pattern = last.get("Pattern", "None")
    if pattern and pattern != "None":
        score += 1
        reasons.append(f"Pattern: {pattern}")

    signal = "BUY" if last["EMA9"] > last["EMA21"] and last["RSI"] < 70 else "SELL"
    emoji = "📈" if signal == "BUY" else "📉"

    signal_data = {
        "timestamp": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M"),
        "symbol": symbol,
        "timeframe": timeframe,
        "signal": signal,
        "score": score,
        "pattern": pattern,
        "rsi": last["RSI"],
        "ema9": last["EMA9"],
        "ema21": last["EMA21"],
        "reasons": "; ".join(reasons),
    }

    chart_path = generate_pro_chart(df, symbol, timeframe, score, signal, reasons)

    if score >= 3:
        msg = (
            f"{emoji} {signal_data['timestamp']} – {symbol} ({timeframe})\n"
            f"Signal: {signal} | Score: {score}\n"
            f"Pattern: {pattern}\n"
            f"RSI: {last['RSI']:.2f} | EMA9: {last['EMA9']:.4f} | EMA21: {last['EMA21']:.4f}\n"
            f"Reasons: {'; '.join(reasons)}"
        )
        await send_telegram_message(msg)
        if chart_path:
            await send_telegram_photo(chart_path)

    log_to_csv(signal_data)
    return [signal_data]

# Aliases for the main function
symbol_strategies = {
    "XAUUSD": lambda symbol, tf: analyze_symbol(symbol, tf),
    "XAGUSD": lambda symbol, tf: analyze_symbol(symbol, tf),
    "EURUSD": lambda symbol, tf: analyze_symbol(symbol, tf),
    "US30M": lambda symbol, tf: analyze_symbol(symbol, tf),
    "INDNASDAQ": lambda symbol, tf: analyze_symbol(symbol, tf),
}