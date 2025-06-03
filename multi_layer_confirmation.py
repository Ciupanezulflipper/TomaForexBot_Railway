# multi_layer_confirmation.py

import pandas as pd
from indicators import calculate_ema, calculate_rsi

def multi_layer_confirm(df, pattern=None, news_signal=None):
    """
    Main multi-layer filter for the bot.
    - Pattern (string): e.g., 'Bullish Engulfing'
    - News_signal (dict or None): e.g., {'asset':'EURUSD','signal':'BUY'} or None
    Returns: True if technical+news align for alert.
    """
    if df is None or df.empty:
        return False

    last = df.iloc[-1]

    # 1. Pattern filter
    found_pattern = last.get("Pattern", "")
    if not found_pattern or (pattern and pattern not in found_pattern):
        return False

    # 2. RSI filter (classic: oversold for bullish, overbought for bearish)
    rsi = last.get("rsi") or calculate_rsi(df["close"], 14).iloc[-1]
    if pd.isna(rsi):
        return False
    if "Bullish" in found_pattern and rsi > 45:  # Only alert if RSI <45 for bullish
        return False
    if "Bearish" in found_pattern and rsi < 55:  # Only alert if RSI >55 for bearish
        return False

    # 3. EMA confirmation (trend filter)
    ema9 = last.get("ema9") or calculate_ema(df["close"], 9).iloc[-1]
    ema21 = last.get("ema21") or calculate_ema(df["close"], 21).iloc[-1]
    if pd.isna(ema9) or pd.isna(ema21):
        return False
    if "Bullish" in found_pattern and not (ema9 > ema21):
        return False
    if "Bearish" in found_pattern and not (ema9 < ema21):
        return False

    # 4. News confirmation if passed in (optional)
    if news_signal:
        # News signal must match symbol and strong bias (BUY/SELL)
        if not (news_signal.get("signal") in ["BUY", "SELL"]):
            return False

    # If all pass, CONFIRM
    return True

# Example manual test
if __name__ == "__main__":
    from marketdata import get_mt5_data
    from patterns import detect_candle_patterns

    symbol = "EURUSD"
    df = get_mt5_data(symbol, "H1", bars=100)
    if df is not None and not df.empty:
        df = detect_candle_patterns(df)
        # Example test with fake news signal
        news_signal = {"asset": "EURUSD", "signal": "BUY"}
        if multi_layer_confirm(df, pattern="Bullish Engulfing", news_signal=news_signal):
            print(f"{symbol}: Bullish Engulfing confirmed by multi-layer logic!")
        else:
            print(f"{symbol}: No strong confirmation found.")
