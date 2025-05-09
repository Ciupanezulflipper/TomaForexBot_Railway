# corelogic.py
from indicators import calculate_ema, calculate_rsi
from patterns import detect_candle_patterns
from logger import log_to_csv  # send_telegram_alert removed for Railway
from fibonacci import calculate_fibonacci_levels, match_fibonacci_price

def analyze_symbol(df, symbol, score_threshold=4):
   df = calculate_ema(df, 9, 21)
    df = calculate_rsi(df, period=14)
    df = detect_candle_patterns(df)

    if df is None or df.empty:
        return []

    last_row = df.iloc[-1]
    price = last_row['close']
    score = 0
    reasons = []

    if last_row['EMA9'] > last_row['EMA21']:
        score += 1
        reasons.append('EMA9 > EMA21')
    elif last_row['EMA9'] < last_row['EMA21']:
        score += 1
        reasons.append('EMA9 < EMA21')

    if 30 < last_row['RSI'] < 70:
        score += 1
        reasons.append('RSI neutral')

    if last_row.get('pattern') in ['Doji', 'Hammer', 'Engulfing']:
        score += 1
        reasons.append('strong pattern')

    fib_levels = calculate_fibonacci_levels(df)
    fib_label, _ = match_fibonacci_price(price, fib_levels)

    if fib_label:
        score += 1
        reasons.append(f"near {fib_label} Fib level")

    if score >= score_threshold:
        direction = 'BUY' if last_row['EMA9'] > last_row['EMA21'] else 'SELL'
        emoji = '📈' if direction == 'BUY' else '📉'
        signal = {
            "symbol": symbol,
            "signal": direction,
            "emoji": emoji,
            "pattern": last_row.get("pattern", ""),
            "rsi": round(last_row['RSI'], 2),
            "ema9": round(last_row['EMA9'], 4),
            "ema21": round(last_row['EMA21'], 4),
            "score": score,
            "reasons": reasons
        }
        log_to_csv(signal)
        send_telegram_alert(f"{emoji} {direction} Signal for {symbol}\nPattern: {signal['pattern']}\nRSI: {signal['rsi']} | EMA9: {signal['ema9']} | EMA21: {signal['ema21']}\nScore: {score} ✅\nReasons: {', '.join(reasons)}")
        return [signal]
    return []
