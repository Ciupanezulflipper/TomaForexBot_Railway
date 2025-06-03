# test_data_retrieval.py


import pandas as pd
from marketdata import connect, disconnect, get_mt5_data

SYMBOL   = "XAUUSD"
TIMEFRAME= "H1"  # 1-hour bars
BARS     = 10                # fetch last 10 bars

def main():
    # 1. Connect
    if not connect():
        print("❌ Connection failed.")
        return

    # 2. Fetch data
    df = get_mt5_data(SYMBOL, timeframe=TIMEFRAME, bars=BARS)
    if df is None or df.empty:
        print(f"⚠️ No data returned for {SYMBOL}")
    else:
        print(f"✅ Retrieved {len(df)} bars for {SYMBOL}")
        print("\n--- DataFrame head ---")
        print(df.head())
        print("\n--- Columns ---")
        print(list(df.columns))

    # 3. Clean up
    disconnect()

if __name__ == "__main__":
    main()
