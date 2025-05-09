from telegrambot import send_telegram_message
from corelogic import analyze_symbol
import pandas as pd
import datetime

def get_mock_data():
    # Simulated OHLCV data (replace this with a real API or CSV if needed)
    now = datetime.datetime.now()
    data = {
        'time': [now - datetime.timedelta(hours=i) for i in range(200)],
        'open': [1.1 + i * 0.01 for i in range(200)],
        'high': [1.2 + i * 0.01 for i in range(200)],
        'low': [1.0 + i * 0.01 for i in range(200)],
        'close': [1.15 + i * 0.01 for i in range(200)],
        'tick_volume': [1000 for _ in range(200)],
    }
    df = pd.DataFrame(data)
    df = df[::-1].reset_index(drop=True)  # reverse to match historical order
    return df

def main():
    symbol = "SIMULATED"
    timeframe = "H1"
    df = get_mock_data()

    print(f"Analyzing {symbol} on timeframe {timeframe}")
    signal = analyze_symbol(symbol, df)

    if signal:
        message = f"📈 Signal for {symbol} on {timeframe}:\n\n{signal}"
        print(message)
        send_telegram_message(message)
    else:
        print("No signal detected.")

if __name__ == "__main__":
    main()
