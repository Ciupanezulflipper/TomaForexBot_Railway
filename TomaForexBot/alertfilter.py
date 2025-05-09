def is_strong_signal(patterns, rsi, rsi_overbought=70, rsi_oversold=30):
    """
    Determines if the combination of detected patterns and RSI value indicates a strong signal.

    Args:
        patterns (list): List of detected candlestick pattern names.
        rsi (float): Latest RSI value.
        rsi_overbought (int): Upper RSI threshold for sell signals.
        rsi_oversold (int): Lower RSI threshold for buy signals.

    Returns:
        bool: True if it's a strong signal, False otherwise.
    """
    if not patterns or "None" in patterns:
        return False

    # Strong BUY: bullish patterns + oversold RSI
    if rsi < rsi_oversold:
        return True

    # Strong SELL: bearish patterns + overbought RSI
    if rsi > rsi_overbought:
        return True

    return False
