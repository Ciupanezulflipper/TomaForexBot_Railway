# Weight configuration for signal scoring

def get_weights():
    return {
        "rsi": 0.25,        # 25% weight
        "pattern": 0.25,    # 25% weight
        "ema": 0.2,         # 20% weight
        "fibonacci": 0.2,   # 20% weight
        "risk": 0.1         # 10% weight
    }
