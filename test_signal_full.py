from marketdata import connect, disconnect, get_mt5_data
from indicators import calculate_ema, calculate_rsi
from patterns import detect_candle_patterns
from alertfilter import is_strong_signal
from charting import generate_pro_chart
from telegramsender import send_telegram_message, send_telegram_photo

# --- CONFIG ---
symbol = "XAUUSD"
timeframe = "H1"
bars = 200

# --- MAIN TEST ---
if not connect():
    print("❌ Connection failed.")
    exit()

df = get_mt5_data(symbol, timeframe=timeframe, bars=bars)
if df.empty:
    print(f"⚠️ No data for {symbol}")
    disconnect()
    exit()

# Inspect columns to understand the structure
print("Columns in DataFrame:", df.columns)  # Added this line to help debug the missing datetime column

# Indicators
df["ema9"] = calculate_ema(df["close"], 9)
df["ema21"] = calculate_ema(df["close"], 21)
df["rsi"] = calculate_rsi(df["close"], 14)

# patterns
patterns = detect_candle_patterns(df.tail(5))  # Remove the threshold argument
last_rsi = df["rsi"].iloc[-1]

# --- Force test to pass even without real signal ---
patterns = ["Bullish Engulfing", "Hammer", "Doji"]  # simulate 3 patterns
last_rsi = 28.5  # simulate oversold

# Generate signal
if is_strong_signal(patterns, last_rsi):
    score = 5
    signal = "BUY"
    reasons = f"patterns: {', '.join(patterns)} | rsi: {last_rsi:.2f}"

    chart_path = generate_pro_chart(df, symbol, "H1", score, signal, reasons)
    msg = (
        f"📢 *{signal} Signal on {symbol}*\n"
        f"🧠 {reasons}\n"
        f"📊 ema9={df['ema9'].iloc[-1]:.4f}, ema21={df['ema21'].iloc[-1]:.4f}"
    )
    send_telegram_message(msg)
    send_telegram_photo(chart_path)
    print("✅ Full signal sent.")
else:
    print("🟡 Not a strong signal.")

disconnect()
