import os
from dotenv import load_dotenv

REQUIRED_KEYS = [
    "TELEGRAM_TOKEN",
    "TELEGRAM_CHAT_ID",
    "NEWS_API_KEY",
    "EXCHANGERATE_API_KEY"
]

def load_env():
    load_dotenv()
    check_env()

def check_env():
    missing = [key for key in REQUIRED_KEYS if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing required .env keys: {', '.join(missing)}")
