import pandas as pd
import numpy as np

def calculate_fibonacci_levels(high, low):
    diff = high - low
    return {
        "0.0%": float(high),
        "23.6%": float(high - 0.236 * diff),
        "38.2%": float(high - 0.382 * diff),
        "50.0%": float(high - 0.5 * diff),
        "61.8%": float(high - 0.618 * diff),
        "100.0%": float(low),
    }

def match_fibonacci_price(price, fib_levels, threshold=0.001):
    # ✅ ensure price is scalar
    if isinstance(price, (pd.Series, np.ndarray)):
        price_val = float(price.iloc[-1]) if isinstance(price, pd.Series) else float(price[-1])
    else:
        price_val = float(price)

    for label, level in fib_levels.items():
        level_val = float(level.values[0]) if hasattr(level, "values") else float(level)
        if abs(price_val - level_val) <= threshold:
            return label
    return None
