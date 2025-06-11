import os
import asyncio
import pandas as pd
from dotenv import load_dotenv
from telegram import Bot
from indicators import calculate_rsi
from patterns import detect_patterns
from marketdata import get_ohlc  # Use this instead of MT5

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

MONITOR_PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
TIMEFRAME = "H1"
MIN_RSI_BUY = 35
MAX_RSI_SELL = 65

bot = Bot(token=TELEGRAM_TOKEN)

async def analyze_and_alert():
    for symbol in MONITOR_PAIRS:
        df = await get_ohlc(symbol, TIMEFRAME, bars=100)

        if df is None or df.empty:
            print(f"[{symbol}] No data.")
            continue

        # --- Standardize columns for pattern detection ---
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })

        patterns = detect_patterns(df)
        last_pattern = ""
        if patterns['bullish_engulfing']:
            last_pattern = "Bullish Engulfing"
        elif patterns['bearish_engulfing']:
            last_pattern = "Bearish Engulfing"
        elif patterns['pin_bar'] == "bullish":
            last_pattern = "Bullish Pin Bar"
        elif patterns['pin_bar'] == "bearish":
            last_pattern = "Bearish Pin Bar"

        rsi = calculate_rsi(df["Close"], 14)
        df["RSI"] = rsi

        last = df.iloc[-1]
        last_rsi = last.get("RSI", None)
        last_close = last.get("Close", None)

        alert = None
        reason = ""

        if last_pattern in ["Bullish Engulfing", "Bullish Pin Bar"]:
            if last_rsi is not None and last_rsi < MIN_RSI_BUY:
                alert = f"BUY Signal on {symbol} ({TIMEFRAME})\nPattern: {last_pattern}\nRSI: {last_rsi:.2f}\nClose: {last_close}"
                reason = "Pattern + RSI oversold"
        if last_pattern in ["Bearish Engulfing", "Bearish Pin Bar"]:
            if last_rsi is not None and last_rsi > MAX_RSI_SELL:
                alert = f"SELL Signal on {symbol} ({TIMEFRAME})\nPattern: {last_pattern}\nRSI: {last_rsi:.2f}\nClose: {last_close}"
                reason = "Pattern + RSI overbought"

        if alert:
            print(f"[ALERT] {alert} ({reason})")
            try:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=alert)
            except Exception as e:
                print(f"Failed to send Telegram alert: {e}")
        else:
            print(f"[{symbol}] No valid pattern + RSI confluence.")

if __name__ == "__main__":
    print("[PATTERN ALERTS] Checking for multi-confirmation...")
    asyncio.run(analyze_and_alert())
