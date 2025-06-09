import pandas as pd
import yfinance as yf

# Load your clean active trades CSV
df = pd.read_csv("active_trades_clean.csv")

# Get live price for a currency pair
def get_live_price(pair):
    ticker = f"{pair}=X"
    data = yf.download(tickers=ticker, period="1d", interval="1m")
    return float(data["Close"].iloc[-1]) if not data.empty else None

# Analyze trades and print results
for _, row in df.iterrows():
    pair = row["pair"]
    trade_type = row["type"].upper()
    entry = float(row["entry_price"])

    live_price = get_live_price(pair)
    if live_price is None:
        print(f"⚠️ Could not fetch price for {pair}")
        continue

    diff = (entry - live_price) if trade_type == "SELL" else (live_price - entry)
    pips = int(diff * 10000)

    print(f"🧾 {pair} {trade_type} | Entry: {entry:.5f} | Price: {live_price:.5f} | P/L: {pips} pips")
    if pips < -30:
        print(f"🚨 ALERT: {pair} is losing {abs(pips)} pips!")
