# core/signal_utils.py

def calculate_signal_score(rsi_score, pattern_score, ema_score, fib_score, risk_score, weights=None):
    """
    Centralized function to calculate the total signal score using configurable weights.
    """
    if weights is None:
        weights = {
            "rsi": 1,
            "pattern": 1,
            "ema": 1,
            "fibonacci": 1,
            "risk": 1
        }

    return (
        weights['rsi'] * rsi_score +
        weights['pattern'] * pattern_score +
        weights['ema'] * ema_score +
        weights['fibonacci'] * fib_score +
        weights['risk'] * risk_score
    )


def score_bar(score: int):
    """
    Format score bar with emoji arrows.
    """
    units = min(abs(score), 5)
    block = "█" * units
    arrow = "🔺" if score > 0 else "🔻"
    return f"{block}{arrow}"
