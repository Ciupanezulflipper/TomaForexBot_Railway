# riskanalysis.py

import pandas as pd

def calculate_volatility(df, period=14):
    df['returns'] = df['close'].pct_change()
    df['volatility'] = df['returns'].rolling(window=period).std() * 100
    return df

def classify_risk_level(df):
    latest_vol = df['volatility'].iloc[-1]
    if latest_vol < 0.5:
        return "🟢 low"
    elif latest_vol < 1.0:
        return "🟡 Medium"
    else:
        return "🔴 high"

def summarize_risk(df):
    df = calculate_volatility(df)
    risk = classify_risk_level(df)
    return f"Market Volatility: {df['volatility'].iloc[-1]:.2f}% – Risk Level: {risk}"
# riskanalysis.py

def evaluate_risk_zone(price, fib_levels):
    """
    Check if price is in a high-risk zone based on Fibonacci levels.
    Returns:
        str: 'LOW', 'MEDIUM', 'HIGH'
    """
    try:
        price = float(price)
        levels = [float(val) for val in fib_levels.values()]
        levels.sort()

        if price <= levels[1] or price >= levels[-2]:
            return "HIGH"
        elif levels[2] <= price <= levels[-3]:
            return "LOW"
        else:
            return "MEDIUM"
    except Exception as e:
        print(f"[ERROR] evaluate_risk_zone: {e}")
        return "UNKNOWN"

