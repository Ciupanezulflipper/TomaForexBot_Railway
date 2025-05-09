# riskanalysis.py

import pandas as pd

def calculate_volatility(df, period=14):
    df['returns'] = df['close'].pct_change()
    df['volatility'] = df['returns'].rolling(window=period).std() * 100
    return df

def classify_risk_level(df):
    latest_vol = df['volatility'].iloc[-1]
    if latest_vol < 0.5:
        return "🟢 Low"
    elif latest_vol < 1.0:
        return "🟡 Medium"
    else:
        return "🔴 High"

def summarize_risk(df):
    df = calculate_volatility(df)
    risk = classify_risk_level(df)
    return f"Market Volatility: {df['volatility'].iloc[-1]:.2f}% – Risk Level: {risk}"
