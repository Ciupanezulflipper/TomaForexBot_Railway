# test_ema9.py

import pandas as pd

def calculate_ema(series, period=9):
    return series.ewm(span=period, adjust=False).mean()

data = {
    'close': [1.123, 1.124, 1.125, 1.127, 1.126, 1.128, 1.130, 1.129, 1.131, 1.134]
}
df = pd.DataFrame(data)
df['ema9'] = calculate_ema(df['close'], 9)
print(df)
print("Columns:", df.columns.tolist())
print("Last row:", df.tail(1).to_dict(orient='records'))
