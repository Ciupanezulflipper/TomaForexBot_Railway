import requests

# Your bot token (keep private)
TOKEN = "7614899540:AAFXtUe9VaM34naAErHzxPz9_BNu8RrxV3M"

# Replace with your actual chat_id after step 4 below
CHAT_ID = "6074056245"

MESSAGE = "📡 Ping received! Your Telegram bot is working, Toma 💬"

def send_ping():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": MESSAGE
    }
    response = requests.post(url, data=data)
    print("Status:", response.status_code)
    print("Response:", response.text)

send_ping()
