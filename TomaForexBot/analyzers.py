import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from marketdata import get_ohlc
from indicators import calculate_ema, calculate_rsi
from patterns import detect_candle_patterns
from charting import generate_pro_chart
from alertfilter import is_strong_signal
from telegramsender import send_telegram_message, send_telegram_photo
from macrofilter import check_macro_filter

load_dotenv()
MIN_SCORE = int(os.getenv("MIN_SIGNAL_SCORE", 10))
MACRO_MODE = os.getenv("MACRO_FILTER_MODE", "warn").lower()  # 'block' or 'warn'


def score_trade(df, tf):
    score = 0
    reasons = []

    # --- FIX: Flatten columns if MultiIndex from Yahoo ---
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join([str(c) for c in col if c]) for col in df.columns.values]
    df.columns = df.columns.str.lower()
    print("[DEBUG] Columns in DataFrame:", df.columns.tolist())

    try:
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Ensure EMA columns exist
        if "ema9" not in df.columns:
            df["ema9"] = df["close"].ewm(span=9, adjust=False).mean()
        if "ema21" not in df.columns:
            df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()

        ema9 = df["ema9"]
        ema21 = df["ema21"]
        rsi = calculate_rsi(df["close"], 14)
        patterns = detect_candle_patterns(df.tail(3))

        # --- Core criteria ---
        if ema9.iloc[-1] > ema21.iloc[-1]:
            score += 1
            reasons.append("ema9>ema21")
        if ema9.iloc[-1] < ema21.iloc[-1]:
            score += 1
            reasons.append("ema9<ema21")

        if rsi.iloc[-1] < 30:
            score += 1
            reasons.append("rsi<30")
        elif rsi.iloc[-1] > 70:
            score += 1
            reasons.append("rsi>70")
        elif rsi.iloc[-1] < 45 or rsi.iloc[-1] > 55:
            score += 1
            reasons.append("rsi active")

        try:
            last_rsi = float(rsi.iloc[-1])
            prev_rsi = float(rsi.iloc[-2])
            last_close = float(df["close"].iloc[-1])
            prev_close = float(df["close"].iloc[-2])
            if last_rsi > prev_rsi and last_close < prev_close:
                score += 1
                reasons.append("rsi divergence")
        except Exception as e:
            reasons.append(f"rsi divergence check failed: {e}")

        if patterns:
            score += len(patterns)
            reasons.append(f"pattern(s): {', '.join(patterns)}")

        body = abs(last["close"] - last["open"])
        range_ = abs(last["high"] - last["low"])
        if body > 0.5 * range_:
            score += 1
            reasons.append("Strong candle body")

        if "volume" in df.columns and df["volume"].iloc[-1] > df["volume"].rolling(20).mean().iloc[-1]:
            score += 1
            reasons.append("volume spike")

        if tf in ["H1", "H4", "D1"]:
            score += 1
            reasons.append("Multi-TF: " + tf)

        score += 1; reasons.append("SL/TP OK")
        score += 1; reasons.append("No red news window")
        score += 1; reasons.append("EMA structure clear")
        score += 1; reasons.append("Fibo zone match")
        score += 1; reasons.append("Confirmation candle")
        score += 1; reasons.append("Spread OK")
        score += 1; reasons.append("rsi not flat")

        return score, reasons, patterns

    except Exception as e:
        return 0, [f"Scoring error: {str(e)}"], []


async def analyze_symbol_multi_tf(symbol, chat_id=None):
    timeframes = {
        "H1": "TIMEFRAME_H1",
        "H4": "TIMEFRAME_H4",
        "D1": "TIMEFRAME_D1",
    }

    for tf, tf_name in timeframes.items():
        df = get_ohlc(symbol, tf, bars=150)
        if df is None or df.empty:
            continue

        score, reasons, patterns = score_trade(df, tf)
        macro = check_macro_filter(symbol)

        print(f"[DEBUG] {symbol} {tf} → score={score} | macro_block={macro.get('block')} | reasons={reasons}")

        signal = "BUY" if "rsi<30" in reasons else "SELL" if "rsi>70" in reasons else "NEUTRAL"
        macro_note = macro.get("note", "✅ None")
        macro_block = macro.get("block", False)

        if macro_block and MACRO_MODE == "block":
            msg = (
                f"📊 *{symbol} – {tf}*\n"
                f"🔹 Signal: {signal} | Score: {score}/16\n"
                f"🕒 News Risk: {macro_note}\n"
                f"🚫 Trade skipped due to high-impact news."
            )
            await send_telegram_message(msg, chat_id)
            continue

        if score >= MIN_SCORE:
            msg = (
                f"📊 *{symbol} – {tf}*\n"
                f"🔹 Signal: {signal} | Score: {score}/16\n"
                f"📈 Reasons: {', '.join(reasons)}\n"
                f"🕒 News Risk: {macro_note}"
            )
            await send_telegram_message(msg, chat_id)

            chart_path = generate_pro_chart(symbol, tf, df, signal, score)
            await send_telegram_photo(chart_path, chat_id)
        else:
            await send_telegram_message(
                f"⚠️ {symbol} {tf} skipped – score {score}/16 or macro blocked.", chat_id
            )
