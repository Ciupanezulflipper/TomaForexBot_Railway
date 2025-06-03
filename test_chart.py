from charting import generate_pro_chart
from marketdata import connect, disconnect, get_mt5_data

#  Step 1: Connect to data source
if not connect():
    exit()

# Step 2: Get data
symbol = "XAUUSD"
df = get_mt5_data(symbol, timeframe="H1", bars=200)
if df is None or df.empty:
    print(f"❌ No data for {symbol}")
    disconnect()
    exit()

# Step 3: Generate chart
score = 4
signal = "BUY"
reasons = "rsi < 30, EMA crossover, pattern match"
chart_path = generate_pro_chart(df, symbol, "H1", score, signal, reasons)

# Step 4: Show path
print(f"✅ Chart saved at: {chart_path}")

# Step 5: Disconnect
disconnect()
