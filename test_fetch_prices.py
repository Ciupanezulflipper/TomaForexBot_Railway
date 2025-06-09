import pandas as pd
import yfinance as yf

# Load and print the columns to debug
df = pd.read_csv("active_trades.csv")
df.columns = df.columns.str.strip().str.lower()  # Normalize column names

print("🔍 CSV Columns found:", df.columns.tolist())
print("🔍 First 3 rows:\n", df.head())

# If 'pair' column exists, continue
if "pair" not in df.columns:
    print("❌ ERROR: 'pair' column not found. Please check your CSV header.")
    exit()

# Extract pairs and format for yfinance
pairs = df["pair"].tolist()
yf_symbols = [pair.upper() + "=X" for pair in pairs]

# Fetch price data
data = yf.download(yf_symbols, period="1d", interval="1m", progress=False, group_by="ticker")

# Display last close price
for symbol in yf_symbols:
    try:
        price = data[symbol]["Close"].dropna().iloc[-1]
        print(f"{symbol}: {price}")
    except Exception as e:
        print(f"⚠️ Error fetching {symbol}: {e}")
