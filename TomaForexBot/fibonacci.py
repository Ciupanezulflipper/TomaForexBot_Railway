import pandas as pd
import numpy as np

def calculate_fibonacci_levels(high, low):
    diff = high - low
    return {
        "0.0%": high,
        "23.6%": high - 0.236 * diff,
        "38.2%": high - 0.382 * diff,
        "50.0%": high - 0.5 * diff,
        "61.8%": high - 0.618 * diff,
        "100.0%": low,
    }

def match_fibonacci_price(price, fib_levels, threshold=0.001):
    # Ensure price is a scalar float
    if isinstance(price, pd.Series):
        price_val = float(price.iloc[-1])
    elif isinstance(price, np.ndarray):
        price_val = float(price[-1])
    else:
        price_val = float(price)

    for label, level in fib_levels.items():
        if abs(price_val - float(level)) <= threshold:
            return label
    return None
