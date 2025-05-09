import pandas as pd
import datetime

# This is a dummy replacement for MetaTrader5's get_mt5_data()
def get_mock_data(symbol="SIMULATED", timeframe="H1", bars=200):
    now = datetime.datetime.now()
    data = {
        'time': [now - datetime.timedelta(hours=i) for i in range(bars)],
        'open': [1.1 + i * 0.001 for i in range(bars)],
        'high': [1.2 + i * 0.001 for i in range(bars)],
        'low': [1.0 + i * 0.001 for i in range(bars)],
        'close': [1.15 + i * 0.001 for i in range(bars)],
        'tick_volume': [1000 for _ in range(bars)],
    }
    df = pd.DataFrame(data)
    df = df[::-1].reset_index(drop=True)
    return df

# Optional fallback to avoid crashing other imports
def get_mt5_data(*args, **kwargs):
    print("⚠️ MetaTrader5 not available — returning mock data.")
    return get_mock_data()
