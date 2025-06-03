def is_strong_signal(patterns, rsi, rsi_overbought=70, rsi_oversold=30):
    """
    Determines if the combination of detected patterns and rsi value indicates a strong signal.

    Args:
        patterns (list): List of detected candlestick pattern names.
        rsi (float): Latest rsi value.
        rsi_overbought (int): Upper rsi threshold for sell signals.
        rsi_oversold (int): lower rsi threshold for buy signals.

    Returns:
        bool: True if it's a strong signal, False otherwise.
    """
    if not patterns or "None" in patterns:
        return False

    # Strong BUY: bullish patterns + oversold rsi
    if rsi < rsi_oversold:
        return True

    # Strong SELL: bearish patterns + overbought rsi
    if rsi > rsi_overbought:
        return True

    return False
