import os
import pandas as pd
import datetime

USE_MOCK = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

if not USE_MOCK:
    try:
        import MetaTrader5 as mt5
        def connect():
            return mt5.initialize()

        def disconnect():
            mt5.shutdown()

        def get_ohlc(symbol="EURUSD", timeframe=mt5.TIMEFRAME_H1, bars=200):
            if not mt5.initialize():
                print("❌ MT5 init failed:", mt5.last_error())
                return pd.DataFrame()
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
            mt5.shutdown()
            if rates is None or len(rates) == 0:
                return pd.DataFrame()
            df = pd.DataFrame(rates)
            df["datetime"] = pd.to_datetime(df["time"], unit="s")
            df.set_index("datetime", inplace=True)
            return df

    except ImportError:
        print("⚠️ MT5 not available, falling back to mock data")
        USE_MOCK = True

if USE_MOCK:
    def connect():
        return True

    def disconnect():
        pass

    def get_ohlc(symbol="SIMULATED", timeframe="H1", bars=200):
        now = datetime.datetime.now()
        data = {
            'time': [now - datetime.timedelta(hours=i) for i in range(bars)],
            'open': [1.1 + i * 0.01 for i in range(bars)],
            'high': [1.2 + i * 0.01 for i in range(bars)],
            'low': [1.0 + i * 0.01 for i in range(bars)],
            'close': [1.15 + i * 0.01 for i in range(bars)],
            'tick_volume': [1000 for _ in range(bars)],
        }
        df = pd.DataFrame(data)
        df = df[::-1].reset_index(drop=True)
        df["datetime"] = pd.to_datetime(df["time"])
        df.set_index("datetime", inplace=True)
        return df

# Universal alias
get_mt5_data = get_ohlc
