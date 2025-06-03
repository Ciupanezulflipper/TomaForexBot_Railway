import asyncio
from telegramsender import send_telegram_message

async def main():
    msg = "✅ Test message from TomaForexBot"
    await send_telegram_message(msg)

if __name__ == "__main__":
    asyncio.run(main())
