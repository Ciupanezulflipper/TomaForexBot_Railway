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

def match_fibonacci_price(price, levels, threshold=0.001):
    for label, level in levels.items():
        if abs(price - level) <= threshold:
            return label
    return None
