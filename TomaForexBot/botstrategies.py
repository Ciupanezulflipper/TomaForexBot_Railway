import pandas as pd
from indicators import calculate_ema, calculate_rsi
from patterns import detect_candle_patterns
from fibonacci import calculate_fibonacci_levels, match_fibonacci_price
from logger import log_to_csv
from charting import generate_pro_chart
from marketdata import get_mt5_data
from telegramsender import send_telegram_message, send_telegram_photo

async def analyze_symbol(df, symbol, timeframe="H1", chat_id=None):
    if df is None or df.empty:
        print(f"❌ No data returned for {symbol}")
        return []

    try:
        print(f"🔧 [1] Starting analysis for {symbol}")
        df = calculate_ema(df)
        print(f"✅ [2] EMA calculated for {symbol}")

        df = calculate_rsi(df)
        print(f"✅ [3] RSI calculated for {symbol}")

        df = detect_candle_patterns(df)
        print(f"✅ [4] Candle patterns detected for {symbol}")

        last = df.iloc[-1]
        score = 0
        reasons = []

        if "EMA9" in last and "EMA21" in last:
            if pd.notnull(last["EMA9"]) and pd.notnull(last["EMA21"]):
                if last["EMA9"] > last["EMA21"]:
                    score += 1
                    reasons.append("EMA9 > EMA21")
                elif last["EMA9"] < last["EMA21"]:
                    score += 1
                    reasons.append("EMA9 < EMA21")
            else:
                reasons.append("EMA values missing")
        else:
            reasons.append("EMA columns not found")

        if "RSI" in last and pd.notnull(last["RSI"]):
            if last["RSI"] < 30:
                score += 1
                reasons.append("RSI oversold")
            elif last["RSI"] > 70:
                score += 1
                reasons.append("RSI overbought")
            else:
                reasons.append("RSI neutral")
        else:
            reasons.append("RSI missing")

        fib_levels = calculate_fibonacci_levels(high=df["high"].max(), low=df["low"].min())
        fib_match = match_fibonacci_price(last["close"], fib_levels)
        if fib_match:
            score += 1
            reasons.append(f"near {fib_match} Fib level")

        pattern = last.get("Pattern", "None")
        if pattern and pattern != "None":
            score += 1
            reasons.append(f"Pattern: {pattern}")

        signal = "BUY" if last.get("EMA9", 0) > last.get("EMA21", 0) and last.get("RSI", 50) < 70 else "SELL"
        emoji = "📈" if signal == "BUY" else "📉"

        signal_data = {
            "timestamp": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M"),
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": signal,
            "score": score,
            "pattern": pattern,
            "rsi": last.get("RSI", 0),
            "ema9": last.get("EMA9", 0),
            "ema21": last.get("EMA21", 0),
            "reasons": "; ".join(reasons),
        }

        print(f"✅ [5] Signal scoring complete for {symbol}")

        chart_path = generate_pro_chart(df, symbol, timeframe, score, signal, reasons)
        print(f"✅ [6] Chart generated for {symbol}")

        if score >= 3:
            msg = (
                f"{emoji} {signal_data['timestamp']} – {symbol} ({timeframe})\n"
                f"Signal: {signal} | Score: {score}\n"
                f"Pattern: {pattern}\n"
                f"RSI: {last.get('RSI', 0):.2f} | EMA9: {last.get('EMA9', 0):.4f} | EMA21: {last.get('EMA21', 0):.4f}\n"
                f"Reasons: {'; '.join(reasons)}"
            )
            await send_telegram_message(msg)
            if chart_path:
                await send_telegram_photo(chart_path)

        log_to_csv(signal_data)
        return [signal_data]

    except Exception as e:
        print(f"❌ ERROR during analyze_symbol for {symbol}: {e}")
        return []


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


# 🔹 Used by /scanall
async def analyze_many_symbols():
    symbols = [
        "XAUUSD", "XAGUSD", "EURUSD", "GBPUSD", "USDJPY",
        "USDCAD", "BTCUSD", "ETHUSD", "SPX500", "US30"
    ]
    messages = []

    for symbol in symbols:
        print(f"🔍 Scanning {symbol}...")
        df = get_mt5_data(symbol, timeframe="H1", bars=200)
        if df is None or df.empty:
            print(f"❌ No data for {symbol}")
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
