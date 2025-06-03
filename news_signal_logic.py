import os
import asyncio
from dotenv import load_dotenv

# --- CONFIG ---
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# Import or define your async Telegram sender
from telegram import Bot

bot = Bot(token=TELEGRAM_TOKEN)

async def send_telegram_message(message, chat_id=TELEGRAM_CHAT_ID):
    try:
        await bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram message: {e}")

# --- News Analysis Logic Example ---

def analyze_news_headline(headline):
    # Very basic logic for the demo. You can expand!
    signals = []

    headline_lower = headline.lower()

    if "tariff" in headline_lower and "delay" in headline_lower:
        signals.append({
            "pair": "US30",
            "signal": "BUY",
            "reason": "Tariff delay is positive for stocks"
        })
        signals.append({
            "pair": "EURUSD",
            "signal": "BUY",
            "reason": "USD weakness expected"
        })
        signals.append({
            "pair": "USDJPY",
            "signal": "HOLD",
            "reason": "No direct impact"
        })
    # Add more rules here as needed

    return signals

async def handle_news_and_alert(headline, chat_id=TELEGRAM_CHAT_ID):
    signals = analyze_news_headline(headline)
    if not signals:
        msg = f"Headline: {headline}\nNo trading signals detected."
        print(msg)
        await send_telegram_message(msg, chat_id)
        return

    msg_lines = [f"Headline: {headline}"]
    for sig in signals:
        msg_lines.append(f"- {sig['pair']}: {sig['signal']} ({sig['reason']})")
    msg = "\n".join(msg_lines)
    print(msg)
    await send_telegram_message(msg, chat_id)

# Manual test
if __name__ == "__main__":
    test_headline = "Trump delays tariffs on Europe until July 9."
    asyncio.run(handle_news_and_alert(test_headline, chat_id=TELEGRAM_CHAT_ID))
    print("Manual test completed.")
