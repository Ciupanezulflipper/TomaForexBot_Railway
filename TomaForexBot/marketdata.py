import MetaTrader5 as mt5
import pandas as pd

def connect():
    if not mt5.initialize():
        print("❌ MT5 init failed:", mt5.last_error())
        return False
    print("✅ Connected to MT5")
    return True

def disconnect():
    mt5.shutdown()
    print("🔌 Disconnected from MT5")

def get_ohlc(symbol, timeframe=mt5.TIMEFRAME_H1, bars=200):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None or len(rates) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    df["datetime"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("datetime", inplace=True)
    return df

# alias for compatibility
get_mt5_data = get_ohlc
