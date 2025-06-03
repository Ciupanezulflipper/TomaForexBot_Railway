# triple_screen_system.py
"""
Implements Elder's Triple Screen system.
Uses three timeframes: Long (trend), Medium (setup), Short (trigger).
Call: triple_screen_signal(df_long, df_med, df_short)
Each df = DataFrame for symbol & timeframe.
"""

import pandas as pd
from indicators import calculate_ema, calculate_rsi

def triple_screen_signal(df_long, df_med, df_short):
    """
    Returns (signal, reasons) where:
    signal = 'BUY', 'SELL', or 'HOLD'
    reasons = list of logic points
    """

    reasons = []

    # 1. Long trend: EMA21 uptrend/downtrend filter (Weekly)
    long_ema21 = calculate_ema(df_long["close"], 21)
    if df_long["close"].iloc[-1] > long_ema21.iloc[-1]:
        major_trend = "UP"
        reasons.append("Major trend UP (long EMA21)")
    elif df_long["close"].iloc[-1] < long_ema21.iloc[-1]:
        major_trend = "DOWN"
        reasons.append("Major trend DOWN (long EMA21)")
    else:
        major_trend = "FLAT"
        reasons.append("Major trend FLAT (long EMA21)")

    # 2. Medium setup: RSI(14) (Daily/H4)
    med_rsi = calculate_rsi(df_med["close"], 14)
    rsi_val = med_rsi.iloc[-1]
    if rsi_val < 30:
        rsi_signal = "OVERSOLD"
        reasons.append("Medium timeframe OVERSOLD (RSI<30)")
    elif rsi_val > 70:
        rsi_signal = "OVERBOUGHT"
        reasons.append("Medium timeframe OVERBOUGHT (RSI>70)")
    else:
        rsi_signal = "NEUTRAL"
        reasons.append("Medium timeframe RSI neutral (30–70)")

    # 3. Short trigger: EMA9/EMA21 crossover or strong candle (H1/M15)
    short_ema9 = calculate_ema(df_short["close"], 9)
    short_ema21 = calculate_ema(df_short["close"], 21)
    if short_ema9.iloc[-1] > short_ema21.iloc[-1]:
        trigger = "BUY"
        reasons.append("Short EMA9 > EMA21 (trigger BUY)")
    elif short_ema9.iloc[-1] < short_ema21.iloc[-1]:
        trigger = "SELL"
        reasons.append("Short EMA9 < EMA21 (trigger SELL)")
    else:
        trigger = "HOLD"
        reasons.append("Short EMA cross flat (no trigger)")

    # Final Logic: Only BUY if trend UP & trigger BUY & not overbought. Only SELL if trend DOWN & trigger SELL & not oversold.
    signal = "HOLD"
    if major_trend == "UP" and trigger == "BUY" and rsi_signal != "OVERBOUGHT":
        signal = "BUY"
        reasons.append("All screens aligned for BUY")
    elif major_trend == "DOWN" and trigger == "SELL" and rsi_signal != "OVERSOLD":
        signal = "SELL"
        reasons.append("All screens aligned for SELL")
    else:
        reasons.append("Screens not aligned, HOLD/no signal")

    return signal, reasons

# USAGE EXAMPLE:
# signal, reasons = triple_screen_signal(df_week, df_day, df_hour)
# print(signal, reasons)
