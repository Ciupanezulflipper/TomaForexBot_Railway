import os
import time
import json
import pandas as pd
import websocket
import yfinance as yf
from dotenv import load_dotenv
from finnhub_data import get_finnhub_data  # Make sure this file exists and works

load_dotenv()

XTB_USER = os.getenv("XTB_USER")
XTB_PASS = os.getenv("XTB_PASS")
XTB_DEMO = True  # Set to False for real account

# === XTB Connector ===
class XTBConnector:
    def __init__(self):
        self.session_id = None
        self.ws = None

    def connect(self):
        try:
            url = "wss://xapi.xtb.com/demo" if XTB_DEMO else "wss://xapi.xtb.com/real"
            self.ws = websocket.WebSocket()
            self.ws.settimeout(5)
            self.ws.connect(url)

            payload = {
                "command": "login",
                "arguments": {
                    "userId": XTB_USER,
                    "password": XTB_PASS
                }
            }
            self.ws.send(json.dumps(payload))
            response = json.loads(self.ws.recv())
            if response.get("status"):
                self.session_id = response["streamSessionId"]
                return True
            return False
        except Exception as e:
            print(f"❌ XTB connection error: {e}")
            return False

    def get_candles(self, symbol="EURUSD", timeframe="H1", limit=200):
        try:
            self.ws.send(json.dumps({
                "command": "getChartLastRequest",
                "arguments": {
                    "info": {
                        "period": 60,
                        "start": int(time.time()) - (limit * 3600),
                        "symbol": symbol
                    }
                }
            }))
            response = json.loads(self.ws.recv())
            candles = response["returnData"]["rateInfos"]
            df = pd.DataFrame({
                "time": [pd.to_datetime(c["ctm"], unit="ms") for c in candles],
                "open": [c["open"] for c in candles],
                "high": [c["high"] for c in candles],
                "low": [c["low"] for c in candles],
                "close": [c["close"] for c in candles],
                "volume": [c["vol"] for c in candles]
            }).set_index("time")
            return df
        except Exception as e:
            print(f"❌ Failed to fetch from XTB: {e}")
            return pd.DataFrame()

xtb = XTBConnector()

# === Yahoo fallback ===
def get_yahoo_data(symbol, bars):
    map_yahoo = {
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "JPY=X",
        "USDCHF": "CHF=X",
        "AUDUSD": "AUDUSD=X",
        "NZDUSD": "NZDUSD=X",
        "USDCAD": "CAD=X",
        "XAUUSD": "GC=F",
        "XAGUSD": "SI=F",
        "BTCUSD": "BTC-USD",
        "ETHUSD": "ETH-USD",
        "US30": "^DJI",
        "NAS100": "^IXIC",
        "SPX500": "^GSPC",
        "WTI": "CL=F",
        "NGAS": "NG=F",
        "COFFEE": "KC=F"
    }

    yf_symbol = map_yahoo.get(symbol, symbol)
    try:
        print(f"🌐 Fetching Yahoo data for {symbol} → {yf_symbol}")
        df = yf.download(tickers=yf_symbol, period="30d", interval="1h", multi_level_index=False)

        # Fallback: flatten columns if still MultiIndex (just in case)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(-1)

        print(f"✅ Yahoo raw data: {len(df)} rows")
        if df.empty:
            print(f"⚠️ Yahoo returned empty for {symbol}")
            return pd.DataFrame()

        # Lowercase and clean up columns
        df.rename(columns={
            "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Volume": "volume",
            "Adj Close": "adj_close"
        }, inplace=True)

        # Drop unwanted columns
        if 'adj_close' in df.columns:
            df.drop(columns=['adj_close'], inplace=True)

        # Final select (some pairs like indices may be missing "volume", handle with dropna)
        cols_needed = ["open", "high", "low", "close", "volume"]
        missing = [c for c in cols_needed if c not in df.columns]
        for c in missing:
            df[c] = None  # Add missing columns with None
        return df[cols_needed].tail(bars)

    except Exception as e:
        print(f"❌ Yahoo error for {symbol}: {e}")
        return pd.DataFrame()

# === Unified fetch function ===
def get_mt5_data(symbol="EURUSD", timeframe="H1", bars=200):
    print(f"🔍 Attempting to fetch {symbol} ({timeframe})...")

    df = pd.DataFrame()

    # Try XTB
    if xtb.connect():
        df = xtb.get_candles(symbol, timeframe, bars)
        if not df.empty:
            print(f"✅ XTB data OK for {symbol}")
    else:
        print(f"⚠️ XTB connection failed.")

    # Try Finnhub
    if df.empty:
        print(f"⚠️ Trying Finnhub for {symbol}...")
        df = get_finnhub_data(symbol, interval=timeframe, limit=bars)
        if not df.empty:
            print(f"✅ Finnhub data OK for {symbol}")

    # Try Yahoo
    if df.empty:
        print(f"⚠️ Trying Yahoo for {symbol}...")
        df = get_yahoo_data(symbol, bars)
        if not df.empty:
            print(f"✅ Yahoo data OK for {symbol}")

    # Fail-safe
    if df.empty:
        print(f"❌ All sources failed for {symbol}")
        return df

    # Normalize to lowercase
    df.columns = df.columns.str.lower()

    # === Calculate indicators ===
    if "close" in df.columns:
        df["ema9"] = df["close"].ewm(span=9, adjust=False).mean()
        df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()

        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))

    return df

# Aliases
get_xtb_data = get_mt5_data
get_ohlc = get_mt5_data

def connect():
    """
    Top-level connect() wrapper for compatibility.
    Calls XTBConnector's connect method.
    """
    return xtb.connect()
