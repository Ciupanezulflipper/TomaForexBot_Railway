import pandas as pd
from botstrategies import analyze_gold

# dummy historical data for testing
data = {
    "open": [1800, 1805, 1810, 1820, 1815],
    "high": [1810, 1815, 1820, 1830, 1825],
    "low": [1795, 1800, 1805, 1810, 1805],
    "close": [1805, 1810, 1815, 1825, 1810],
    "volume": [1000, 1500, 1200, 1600, 1300]
}
df = pd.DataFrame(data)

# mock indicator functions (if needed for testing)
from indicators import calculate_ema, calculate_rsi
from patterns import detect_candle_patterns, is_strong_signal

def fake_ema(df, short=9, long=21):
    df['ema9'] = df['close'].ewm(span=short, adjust=False).mean()
    df['ema21'] = df['close'].ewm(span=long, adjust=False).mean()
    return df

def fake_rsi(df, period=14):
    df['rsi'] = 50  # neutral for test
    return df

def fake_patterns(df):
    df['pattern'] = 'Doji'
    return df

def fake_strong_signal(row):
    return True

# override with fakes
calculate_ema = fake_ema
calculate_rsi = fake_rsi
detect_candle_patterns = fake_patterns
is_strong_signal = fake_strong_signal

# run test
results = analyze_gold(df)
print(results)
