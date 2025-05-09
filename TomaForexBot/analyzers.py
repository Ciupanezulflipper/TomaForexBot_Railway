# analyzers.py

from marketdata import get_mt5_data  # now mapped to mock data
from indicators import calculate_ema, calculate_rsi
from patterns import detect_candle_patterns
from charting import generate_pro_chart
from alertfilter import is_strong_signal
from telegramsender import send_telegram_message, send_telegram_photo

async def analyze_symbol_multi_tf(symbol, chat_id=None):
    timeframes = {
        "H1": "TIMEFRAME_H1",
        "H4": "TIMEFRAME_H4",
        "D1": "TIMEFRAME_D1",
    }

    signals = []

    for tf, tf_name in timeframes.items():
        df = get_ohlc(symbol, tf, bars=150)
        if df is None or df.empty:
            continue

        df["EMA9"] = calculate_ema(df["close"], 9)
        df["EMA21"] = calculate_ema(df["close"], 21)
        df["RSI"] = calculate_rsi(df["close"], 14)

        patterns = detect_candle_patterns(df.tail(3))
        last_rsi = df.iloc[-1]["RSI"]
        signal_strength = is_strong_signal(patterns, last_rsi)

        signal = {
            "symbol": symbol,
            "timeframe": tf,
            "rsi": round(last_rsi, 2),
            "patterns": patterns,
            "score": len(patterns),
            "signal": "BUY" if last_rsi < 30 else "SELL" if last_rsi > 70 else "NEUTRAL",
            "strong": signal_strength,
        }

        signals.append(signal)

        if signal_strength:
            msg = (
                f"📊 *{symbol} – {tf}*\n"
                f"🔹 Signal: {signal['signal']} | Score: {signal['score']}\n"
                f"🧠 Patterns: {', '.join(patterns)}\n"
                f"📉 RSI: {signal['rsi']}"
            )
            await send_telegram_message(msg, chat_id)
            chart_path = generate_pro_chart(df, symbol, tf, signal["score"], signal["signal"], signal["patterns"])
            await send_telegram_photo(chart_path, chat_id)

    if not any(s["strong"] for s in signals):
        await send_telegram_message(f"⚠️ No strong signals found for {symbol}.", chat_id)
