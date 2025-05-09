
import asyncio
import time
from marketdata import connect, get_mt5_data
from botstrategies import symbol_strategies
from telegrambot import start_telegram_listener, send_telegram_message

# ✅ Launch Telegram listener (runs async)
async def main():
    print("🤖 Bot is running... sending help menu to Telegram.")
    await send_telegram_message("🤖 TomaForexBot is now running...")
    await start_telegram_listener()

# ✅ Connect to MT5
if not connect():
    print("❌ Failed to connect to MetaTrader 5")
    exit()

# ✅ Run Telegram bot listener in background
loop = asyncio.get_event_loop()
loop.create_task(main())

# ✅ Scheduled signal analysis loop
while True:
    print("🔄 Running scheduled analysis...")
    for symbol, analyzer in symbol_strategies.items():
        df = get_mt5_data(symbol, timeframe=mt5.TIMEFRAME_H1, bars=200)
        if df is not None and not df.empty:
            try:
                asyncio.run(analyzer(df, symbol))
            except Exception as e:
                print(f"⚠️ Error analyzing {symbol}: {e}")
        else:
            print(f"❌ No data returned for {symbol}")
    print("✅ Analysis complete. Waiting 15 minutes...\n")
    time.sleep(900)
