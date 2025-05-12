import pandas as pd
from indicators import calculate_ema, calculate_rsi
from patterns import detect_candle_patterns
from fibonacci import calculate_fibonacci_levels, match_fibonacci_price
from logger import log_to_csv
from charting import generate_pro_chart
from marketdata import get_mt5_data

# 🔍 Core analysis function
async def analyze_symbol(df, symbol, timeframe="H1"):
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

    # Generate chart (optional chart_path usage in Telegram)
    generate_pro_chart(df, symbol, timeframe, score, signal, reasons)

    log_to_csv(signal_data)
    return [signal_data]

# 🔹 Used by /gold, /us30
async def analyze_symbol_single(symbol, timeframe="H1"):
    df = get_mt5_data(symbol, timeframe, bars=200)
    if df is None or df.empty:
        return f"❌ No data for {symbol}"

    results = await analyze_symbol(df, symbol, timeframe)
    if not results:
        return f"❌ No signal for {symbol}"

    r = results[0]
    emoji = "📈" if r["signal"] == "BUY" else "📉"
    return (
        f"{emoji} {r['timestamp']} – {r['symbol']} ({r['timeframe']})\n"
        f"Signal: {r['signal']} | Score: {r['score']}\n"
        f"Pattern: {r['pattern']}\n"
        f"RSI: {r['rsi']:.2f} | EMA9: {r['ema9']:.4f} | EMA21: {r['ema21']:.4f}\n"
        f"Reasons: {r['reasons']}"
    )

# 🔹 Used by /analyze (multi-symbol)
async def analyze_all_symbols():
    symbols = ["XAUUSD", "XAGUSD", "EURUSD", "US30", "GBPJPY"]
    messages = []

    for symbol in symbols:
        df = get_mt5_data(symbol, timeframe="H1", bars=200)
        if df is None or df.empty:
            messages.append(f"❌ {symbol}: No data")
            continue

        results = await analyze_symbol(df, symbol, "H1")
        if not results:
            messages.append(f"❌ {symbol}: No signal")
            continue

        r = results[0]
        emoji = "📈" if r["signal"] == "BUY" else "📉"
        messages.append(
            f"{emoji} {r['symbol']} ({r['timeframe']})\n"
            f"Signal: {r['signal']} | Score: {r['score']}\n"
            f"RSI: {r['rsi']:.2f}, Pattern: {r['pattern']}\n"
            f"Reasons: {r['reasons']}"
        )

    return messages

async def analyze_many_symbols():
    symbols = [
        "XAUUSD", "XAGUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
        "AUDUSD", "NZDUSD", "EURJPY", "GBPJPY", "EURGBP", "USDCAD",
        "BTCUSD", "ETHUSD", "US30", "NAS100", "SPX500", "WTI", "NGAS", "COFFEE"
    ]
    messages = []

    for symbol in symbols:
        df = get_mt5_data(symbol, timeframe="H1", bars=200)
        if df is None or df.empty:
            messages.append(f"❌ {symbol}: No data")
            continue

        results = await analyze_symbol(df, symbol, "H1")
        if not results:
            messages.append(f"❌ {symbol}: No signal")
            continue

        r = results[0]
        emoji = "📈" if r["signal"] == "BUY" else "📉"
        messages.append(
            f"{emoji} {r['symbol']} ({r['timeframe']})\n"
            f"Signal: {r['signal']} | Score: {r['score']}\n"
            f"RSI: {r['rsi']:.2f}, Pattern: {r['pattern']}\n"
            f"Reasons: {r['reasons']}"
        )

    return messages

