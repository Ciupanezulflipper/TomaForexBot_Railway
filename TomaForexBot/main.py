# TomaForexBot/main.py

# Trigger rebuild

import threading
import uvicorn
import asyncio
import nest_asyncio  # 👈 new import
from telegrambot import start_telegram_listener
from api_receiver import app

nest_asyncio.apply()  # 👈 apply patch for Windows

def run_telegram():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_telegram_listener())

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    t1 = threading.Thread(target=run_telegram)
    t1.start()

    run_api()
