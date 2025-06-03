# weights_config.py

# Scoring Weights (default values)
SCORING_WEIGHTS = {
    "ema_cross": 2,
    "rsi_neutral": 1,
    "strong_pattern": 2,
    "fib_match": 1,
    "volume_spike": 1
}

# Signal threshold (only alert if score >= this)
MINIMUM_SCORE = 4
