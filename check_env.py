from dotenv import load_dotenv
import os

# Load the .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

# Fetch the variables
telegram_token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
tv_user = os.getenv("TRADINGVIEW_USERNAME")
tv_pass = os.getenv("TRADINGVIEW_PASSWORD")

# Print what we got
print("🔍 Checking .env values:")
print("TELEGRAM_TOKEN:", "✅ Loaded" if telegram_token else "❌ MISSING")
print("TELEGRAM_CHAT_ID:", "✅ Loaded" if chat_id else "❌ MISSING")
print("TRADINGVIEW_USERNAME:", tv_user if tv_user else "❌ MISSING")
print("TRADINGVIEW_PASSWORD:", "✅ Loaded" if tv_pass else "❌ MISSING")
