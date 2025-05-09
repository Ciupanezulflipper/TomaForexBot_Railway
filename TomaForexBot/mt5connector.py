import MetaTrader5 as mt5
import pandas as pd

def connect_to_mt5():
    if not mt5.initialize():
        raise RuntimeError(f"❌ MT5 Initialization failed: {mt5.last_error()}")
    print("✅ Connected to MT5.")

def get_latest_data(symbol="XAGUSD", timeframe=mt5.TIMEFRAME_M1, bars=50):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def shutdown_mt5():
    mt5.shutdown()
