
from marketdata import get_ohlc
import asyncio
from indicators import calculate_ema, calculate_rsi
from patterns import detect_candle_patterns
from alertfilter import is_strong_signal
from core.utils import send_telegram_message
from datetime import datetime
import time

def analyze_and_alert(symbol, tf="H1", bars=50, pattern_threshold=2):
    print(f"🔍 Analyzing {symbol}...")

    df = asyncio.run(get_ohlc(symbol, tf, bars=bars))
    if df.empty:
        print(f"⚠️ No data for {symbol}")
        return

    df['ema9'] = calculate_ema(df['close'], period=9)
    df['ema21'] = calculate_ema(df['close'], period=21)
    df['rsi'] = calculate_rsi(df['close'], period=14)

    df = detect_candle_patterns(df)
    patterns = df.tail(pattern_threshold)["Pattern"].tolist()
    last_rsi = df.iloc[-1]['rsi']

    if not is_strong_signal(patterns, last_rsi):
        print(f"🟡 No strong signal for {symbol}.")
        return

    # Compose alert message
    last_time = df.index[-1].strftime('%Y-%m-%d %H:%M')
    emoji = "🚀" if last_rsi < 30 else "🔻" if last_rsi > 70 else "⚖️"
    message = (
        f"📢 *Strong Signal on {symbol}*\n"
        f"🕰 {last_time}\n"
        f"🧠 patterns: {', '.join(patterns)}\n"
        f"📉 rsi: {last_rsi:.2f} {emoji}\n"
        f"🔁 Timeframe: H1"
    )
    send_telegram_message(message)
    print(f"✅ Signal alert sent for {symbol}.\n")

# 🚀 Run all three symbols
def run_all():
    print("🔗 Skipping connect() — using cloud data sources.")

    analyze_and_alert("XAUUSD")
    analyze_and_alert("XAGUSD")
    analyze_and_alert("EURUSD")


      # disconnect()  # disconnect not implemented in async version

# 🕒 Optional loop every hour (disabled by default)
# while True:
#     run_all()
#     time.sleep(3600)  # Wait 1 hour

# ▶️ Run once
if __name__ == "__main__":
    print("🔁 Running scheduled scan at", datetime.now().strftime("%Y-%m-%d %H:%M"))
    run_all()
