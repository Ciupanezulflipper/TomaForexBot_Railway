"""
Fibonacci utilities for trading signal analysis.

- Type annotations and comprehensive docstrings.
- Explicit scalar input/output.
- Configurable threshold for matching.
- Returns closest level and relative "zone" for risk analysis.
- More testable and robust against input errors.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Union

def calculate_fibonacci_levels(high: float, low: float) -> Dict[str, float]:
    """
    Calculate standard Fibonacci retracement levels between high and low.

    Args:
        high (float): The high price value.
        low (float): The low price value.

    Returns:
        dict: Level name to price mapping (e.g., {'0.0%': ..., '23.6%': ..., ...}).
    """
    diff = high - low
    return {
        "0.0%": float(high),
        "23.6%": float(high - 0.236 * diff),
        "38.2%": float(high - 0.382 * diff),
        "50.0%": float(high - 0.5 * diff),
        "61.8%": float(high - 0.618 * diff),
        "100.0%": float(low),
    }

def match_fibonacci_price(
    price: Union[float, pd.Series, np.ndarray],
    fib_levels: Dict[str, float],
    threshold: float = 0.001
) -> Optional[str]:
    """
    Find the Fibonacci level label that matches a given price within a threshold.

    Args:
        price (float or Series/ndarray): Price to match (last value taken if Series/ndarray).
        fib_levels (dict): Output of calculate_fibonacci_levels.
        threshold (float): The allowed price difference for a match.

    Returns:
        str or None: The label (e.g., "50.0%") if within threshold, else None.
    """
    # Ensure price is a scalar float
    if isinstance(price, (pd.Series, np.ndarray)):
        price_val = float(price.iloc[-1]) if isinstance(price, pd.Series) else float(price[-1])
    else:
        price_val = float(price)

    for label, level in fib_levels.items():
        level_val = float(level.values[0]) if hasattr(level, "values") else float(level)
        if abs(price_val - level_val) <= threshold:
            return label
    return None

def closest_fibonacci_level(
    price: Union[float, pd.Series, np.ndarray],
    fib_levels: Dict[str, float]
) -> Tuple[str, float]:
    """
    Find the closest Fibonacci level to the current price.

    Args:
        price (float or Series/ndarray): Price to compare.
        fib_levels (dict): Fibonacci levels as produced by calculate_fibonacci_levels.

    Returns:
        tuple: (closest_level_label, difference)
    """
    if isinstance(price, (pd.Series, np.ndarray)):
        price_val = float(price.iloc[-1]) if isinstance(price, pd.Series) else float(price[-1])
    else:
        price_val = float(price)
    min_diff = float('inf')
    closest_label = ""
    for label, level in fib_levels.items():
        level_val = float(level.values[0]) if hasattr(level, "values") else float(level)
        diff = abs(price_val - level_val)
        if diff < min_diff:
            min_diff = diff
            closest_label = label
    return closest_label, min_diff

def fibonacci_zone(
    price: Union[float, pd.Series, np.ndarray],
    fib_levels: Dict[str, float]
) -> str:
    """
    Classify price into a Fibonacci "zone" for risk analysis.

    Args:
        price (float or Series/ndarray): Price to classify.
        fib_levels (dict): Fibonacci levels as produced by calculate_fibonacci_levels.

    Returns:
        str: One of "above 0%", "0%-23.6%", "23.6%-38.2%", "38.2%-50.0%", "50.0%-61.8%", "61.8%-100%", "below 100%".
    """
    level_keys = ["0.0%", "23.6%", "38.2%", "50.0%", "61.8%", "100.0%"]
    levels = [fib_levels[k] for k in level_keys]
    if isinstance(price, (pd.Series, np.ndarray)):
        price_val = float(price.iloc[-1]) if isinstance(price, pd.Series) else float(price[-1])
    else:
        price_val = float(price)

    if price_val > levels[0]:
        return "above 0%"
    for i in range(len(levels) - 1):
        upper = levels[i]
        lower = levels[i+1]
        if upper >= price_val > lower:
            return f"{level_keys[i]}-{level_keys[i+1]}"
    if price_val <= levels[-1]:
        return "below 100%"
    return "unknown"

def get_fibonacci_levels(price: float, direction: str = "up") -> Dict[str, float]:
    """
    Estimate Fibonacci levels for a move in a direction from price.

    Args:
        price (float): Current price.
        direction (str): "up" (default) or "down".

    Returns:
        dict: Level name to price mapping.
    """
    if direction == "up":
        high = price
        low = price * 0.9  # Estimate; for real use, use historical swing low
    elif direction == "down":
        high = price * 1.1
        low = price
    else:
        raise ValueError("Direction must be 'up' or 'down'")
    return calculate_fibonacci_levels(high, low)