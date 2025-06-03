# configsettings.py

TIMEFRAMES = ["M15", "H1", "H4", "D1"]
DEFAULT_TIMEFRAME = "H1"

SYMBOLS = [
    "EURUSD",
    "XAUUSD",
    "XAGUSD",
    "US30M",
    "INDNASDAQ"
]

CANDLE_PATTERNS = [
    "Bullish Engulfing",
    "Bearish Engulfing",
    "Hammer",
    "Doji"
]

SCORE_THRESHOLD = 3  # Minimum score to send chart + signal
