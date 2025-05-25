import pandas as pd
from patterns import detect_candle_patterns

data = {
    "open": [1800, 1805, 1810, 1820, 1815],
    "high": [1810, 1815, 1820, 1830, 1825],
    "low": [1795, 1800, 1805, 1810, 1805],
    "close": [1805, 1810, 1815, 1825, 1810],
}
df = pd.DataFrame(data)
patterns = detect_candle_patterns(df)
print("Patterns:", patterns)
