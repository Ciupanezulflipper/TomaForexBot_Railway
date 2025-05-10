import asyncio
import uvicorn
from telegrambot import start_telegram_listener
from api_receiver import app

def launch_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    await asyncio.gather(
        start_telegram_listener(),
        asyncio.to_thread(launch_api)
    )

if __name__ == "__main__":
    asyncio.run(main())
