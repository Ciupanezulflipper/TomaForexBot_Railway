# riskmetrics.py
import numpy as np

def calc_atr(df, period=14):
    df = df.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    tr = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    return tr.rolling(window=period).mean().iloc[-1]

def volatility_position_size(account_balance, risk_pct, atr, pip_value):
    risk_amount = account_balance * risk_pct
    if atr == 0 or pip_value == 0:
        return 0
    lots = risk_amount / (atr * pip_value)
    return lots

def sharpe_ratio(df):
    returns = df['Close'].pct_change().dropna()
    if len(returns) < 2:
        return 0
    return (returns.mean() / returns.std()) * np.sqrt(252)
