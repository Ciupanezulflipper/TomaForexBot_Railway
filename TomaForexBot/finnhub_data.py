import requests
import pandas as pd
import os
from datetime import datetime

API_KEY = os.getenv("FINNHUB_API_KEY")

def get_finnhub_data(symbol="EURUSD", interval="H1", limit=150):
    """
    Fetch OHLC data from Finnhub for Forex or indices.
    """
    base_url = "https://finnhub.io/api/v1/forex/candle"

    symbol_map = {
        "EURUSD": "OANDA:EUR_USD",
        "GBPUSD": "OANDA:GBP_USD",
        "USDJPY": "OANDA:USD_JPY",
        "USDCHF": "OANDA:USD_CHF",
        "AUDUSD": "OANDA:AUD_USD",
        "NZDUSD": "OANDA:NZD_USD",
        "USDCAD": "OANDA:USD_CAD",
        "XAUUSD": "OANDA:XAU_USD",
        "XAGUSD": "OANDA:XAG_USD",
        "US30": "FOREXCOM:DJI",
        "NAS100": "FOREXCOM:NSX",
        "SPX500": "FOREXCOM:SPX",
    }

    mapped_symbol = symbol_map.get(symbol.upper())
    if not mapped_symbol:
        print(f"⚠️ Finnhub: Symbol {symbol} not supported.")
        return pd.DataFrame()

    resolution_map = {
        "M1": "1", "M5": "5", "M15": "15", "M30": "30",
        "H1": "60", "H4": "240", "D1": "D"
    }

    resolution = resolution_map.get(interval.upper(), "60")
    now = int(datetime.utcnow().timestamp())
    past = now - limit * 3600  # adjust for H1 granularity

    url = f"{base_url}?symbol={mapped_symbol}&resolution={resolution}&from={past}&to={now}&token={API_KEY}"

    try:
        res = requests.get(url)
        data = res.json()

        if "c" not in data or not data["c"]:
            print(f"⚠️ No data from Finnhub for {symbol}")
            return pd.DataFrame()

        df = pd.DataFrame({
            "time": pd.to_datetime(data["t"], unit="s"),
            "open": data["o"],
            "high": data["h"],
            "low": data["l"],
            "close": data["c"],
            "volume": data["v"]
        }).set_index("time")

        # Rename to match capitalized style in rest of project
        df.rename(columns={
            "open": "open", "high": "high",
            "low": "low", "close": "close",
            "volume": "volume"
        }, inplace=True)

        return df

    except Exception as e:
        print(f"❌ Finnhub error: {e}")
        return pd.DataFrame()
