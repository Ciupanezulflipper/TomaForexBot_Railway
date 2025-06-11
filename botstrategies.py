import os
import asyncio
import pandas as pd
from indicators import calculate_ema, calculate_rsi
from patterns import detect_candle_patterns
from fibonacci import calculate_fibonacci_levels, match_fibonacci_price
from logger import log_to_csv
from charting import generate_pro_chart
from marketdata import get_ohlc
from telegramsender import send_telegram_message, send_telegram_photo

print("🧪 botstrategies.py loaded from", __file__)

async def analyze_symbol(df, symbol, timeframe="H1", chat_id=None):
    if df is None or df.empty:
        print(f"❌ No data returned for {symbol}")
        return []

    df.columns = df.columns.str.lower()

    try:
        print(f"🔧 [1] Starting analysis for {symbol}")
        df["ema9"] = calculate_ema(df["close"], 9)
        df["ema21"] = calculate_ema(df["close"], 21)
        df["rsi"] = calculate_rsi(df["close"], 14)
        df = detect_candle_patterns(df)

        last = df.iloc[-1]
        pattern = last.get('pattern', 'Unknown')

        ema9 = last.get("ema9")
        ema21 = last.get("ema21")
        rsi_val = last.get("rsi")

        # ✅ Safe float conversion
        ema9 = float(ema9) if pd.notnull(ema9) else 0.0
        ema21 = float(ema21) if pd.notnull(ema21) else 0.0
        rsi = float(rsi_val) if pd.notnull(rsi_val) and not isinstance(rsi_val, pd.Series) else 0.0

        # Fix: Pass correct float to Fibonacci + risk analysis
        last_price = float(df["close"].iloc[-1])
        fib = calculate_fibonacci_levels(last_price)
        risk_zone = match_fibonacci_price(last_price, fib)

        signal = "BUY" if ema9 > ema21 else "SELL"
        emoji = "📈" if signal == "BUY" else "📉"
        reasons = [pattern, f"risk: {risk_zone}"]
        score = 1  # Placeholder for your real scoring logic

        signal_data = {
            "timestamp": str(last.name),
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": signal,
            "score": score,
            "pattern": pattern,
            "rsi": rsi,
            "ema9": ema9,
            "ema21": ema21,
            "reasons": reasons
        }

        chart_path = generate_pro_chart(df, symbol, timeframe, score, signal, reasons)
        print(f"✅ [4] Chart generated for {symbol}")

        if score >= 3:
            msg = (
                f"{emoji} {signal_data['timestamp']} – {symbol} ({timeframe})\n"
                f"Signal: {signal} | Score: {score}\n"
                f"pattern: {pattern}\n"
                f"rsi: {rsi:.2f} | ema9: {ema9:.4f} | ema21: {ema21:.4f}\n"
                f"Reasons: {'; '.join(reasons)}"
            )
            await send_telegram_message(msg, chat_id)
            if chart_path:
                await send_telegram_photo(chat_id, chart_path)

        log_to_csv(signal_data)
        return [signal_data]

    except Exception as e:
        print(f"❌ ERROR during analyze_symbol for {symbol}: {e}")
        return []

# 🔹 Single symbol analysis entry point
async def analyze_symbol_single(symbol, timeframe="H1"):
    df = await get_ohlc(symbol, timeframe, bars=200)
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
        f"pattern: {r['pattern']}\n"
        f"rsi: {r['rsi']:.2f} | ema9: {r['ema9']:.4f} | ema21: {r['ema21']:.4f}\n"
        f"Reasons: {r['reasons']}"
    )

# 🔹 Multiple symbol scanner
async def analyze_many_symbols():
    symbols = [
        "XAUUSD", "XAGUSD", "EURUSD", "GBPUSD", "USDJPY",
        "USDCAD", "BTCUSD", "ETHUSD", "SPX500", "US30"
    ]
    messages = []

    for symbol in symbols:
        print(f"🔍 Scanning {symbol}...")
        df = await get_ohlc(symbol, timeframe="H1", bars=200)
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
            f"rsi: {r['rsi']:.2f}, pattern: {r['pattern']}\n"
            f"Reasons: {r['reasons']}"
        )

    return messages

# 🟡 Entry points for commands
def analyze_gold(timeframe="H1", pattern_threshold=2):
    return asyncio.run(analyze_symbol_single("XAUUSD", timeframe))

def analyze_silver(timeframe="H1", pattern_threshold=2):
    return asyncio.run(analyze_symbol_single("XAGUSD", timeframe))

def analyze_silver_alert(timeframe="H1", pattern_threshold=2):
    return analyze_silver(timeframe, pattern_threshold)

def analyze_eurusd(timeframe="H1", pattern_threshold=2):
    return asyncio.run(analyze_symbol_single("EURUSD", timeframe))

def analyze_all(timeframe="H1", pattern_threshold=2):
    results = []
    for symbol in ["XAUUSD", "XAGUSD", "EURUSD"]:
        results.append(asyncio.run(analyze_symbol_single(symbol, timeframe)))
    return "\n\n".join(results)
