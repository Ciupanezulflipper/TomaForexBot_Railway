# TomaForexBot/main.py

import threading
import uvicorn
from telegrambot import start_telegram_listener
from api_receiver import app

def run_telegram():
    import asyncio
    asyncio.run(start_telegram_listener())

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # Launch Telegram in a thread, and API in main process
    t1 = threading.Thread(target=run_telegram)
    t1.start()

    run_api()
