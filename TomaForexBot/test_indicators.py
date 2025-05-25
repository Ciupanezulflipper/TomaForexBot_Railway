import pandas as pd
from indicators import calculate_ema, calculate_rsi

data = {
    "close": [1800, 1805, 1810, 1820, 1815, 1822, 1828, 1835, 1820, 1812]
}
df = pd.DataFrame(data)

ema9 = calculate_ema(df["close"], 9)
ema21 = calculate_ema(df["close"], 21)
rsi = calculate_rsi(df["close"], 14)

print("EMA9:", ema9.tail())
print("EMA21:", ema21.tail())
print("RSI:", rsi.tail())
