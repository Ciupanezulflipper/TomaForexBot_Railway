# telegramalert.py (patch to avoid crashing if telegrambot isn't initialized yet)

try:
    from telegrambot import send_telegram_message
except ImportError:
    def send_telegram_message(msg):
        print("[DEBUG] Telegram not set up, fallback to print:", msg)

from secure_env_loader import load_env
from patterns import detect_patterns
from marketdata import get_ohlc

load_env()

def send_pattern_alerts(symbol: str, timeframe: str = 'H1'):
    try:
        ohlc = get_ohlc(symbol, timeframe)
        patterns = detect_patterns(ohlc)

        if patterns:
            message = f"📌 Pattern Alert for {symbol} [{timeframe}]:\n"
            message += '\n'.join([f"- {p}" for p in patterns])
            send_telegram_message(message)
        else:
            print(f"No patterns detected for {symbol} [{timeframe}].")

    except Exception as e:
        print(f"Error in send_pattern_alerts: {e}")


def send_news_and_events(symbol: str):
    message = f"📰 Placeholder: No live news API logic yet for {symbol}."
    send_telegram_message(message)
