import os
from secure_env_loader import load_env
from patterns import detect_patterns
from marketdata import get_ohlc
from telegramsender import send_telegram_message

load_env()
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

async def send_pattern_alerts(symbol: str, timeframe: str = 'H1'):
    try:
        ohlc = await get_ohlc(symbol, timeframe)
        patterns = detect_patterns(ohlc)

        if patterns:
            message = f"\ud83d\udccc Pattern Alert for {symbol} [{timeframe}]:\n"
            message += '\n'.join([f"- {p}" for p in patterns])
            await send_telegram_message(message, TELEGRAM_CHAT_ID)
        else:
            print(f"No patterns detected for {symbol} [{timeframe}].")

    except Exception as e:
        print(f"Error in send_pattern_alerts: {e}")


async def send_news_and_events(symbol: str):
    try:
        message = f"\ud83d\udcf0 Placeholder: No live news API logic yet for {symbol}."
        await send_telegram_message(message, TELEGRAM_CHAT_ID)
    except Exception as e:
        print(f"Error in send_news_and_events: {e}")
