import os
import requests
from secure_env_loader import load_env

load_env()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Must be set in your .env

def send_alert_message(text: str):
    """Send plain text message to Telegram chat."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Telegram token or chat ID not set.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"⚠️ Telegram alert failed: {response.text}")
        else:
            print("📤 Alert sent to Telegram.")
    except Exception as e:
        print(f"❌ Error sending Telegram alert: {str(e)}")
