import pandas as pd


def is_strong_signal(
    patterns,
    rsi,
    rsi_overbought=70,
    rsi_oversold=30,
    min_score=2,
    verbose=True
):
    """
    Evaluates if detected candle patterns + RSI confirm a strong trade signal.

    Args:
        patterns (list or DataFrame): List of candlestick pattern names.
        rsi (float): Most recent RSI value.
        rsi_overbought (int): RSI above this → overbought zone.
        rsi_oversold (int): RSI below this → oversold zone.
        min_score (int): Minimum confirmation score required.
        verbose (bool): Print debug messages if True.

    Returns:
        bool: True if strong signal, False otherwise.
    """

    # Normalize patterns
    if isinstance(patterns, pd.DataFrame):
        patterns = patterns.get("pattern", []).tolist()
    if not isinstance(patterns, list):
        if verbose:
            print("[DEBUG] Invalid pattern type")
        return False

    # Clean pattern list
    patterns = [p for p in patterns if p and p != "None"]
    if not patterns:
        if verbose:
            print("[DEBUG] No valid candle patterns")
        return False

    # Initialize score
    score = 0

    # Pattern scoring
    for p in patterns:
        if "Bullish" in p:
            score += 1
            if verbose:
                print(f"[+1] Bullish pattern detected: {p}")
        elif "Bearish" in p:
            score += 1
            if verbose:
                print(f"[+1] Bearish pattern detected: {p}")
        elif "pin bar" in p:
            score += 1
            if verbose:
                print(f"[+1] Pin bar pattern detected: {p}")

    # RSI scoring
    if rsi < rsi_oversold:
        score += 1
        if verbose:
            print(f"[+1] RSI = {rsi:.2f} → Oversold")
    elif rsi > rsi_overbought:
        score += 1
        if verbose:
            print(f"[+1] RSI = {rsi:.2f} → Overbought")
    else:
        if verbose:
            print(f"[DEBUG] RSI in neutral zone ({rsi:.2f})")

    # Final decision
    if score >= min_score:
        if verbose:
            print(f"[✔] Strong signal confirmed (score={score})")
        return True
    else:
        if verbose:
            print(f"[✘] Not enough confirmation (score={score})")
        return False
