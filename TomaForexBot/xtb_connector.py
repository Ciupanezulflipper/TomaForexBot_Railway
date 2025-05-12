# xtb_connector.py

import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

XTB_API_URL = "https://xapi.xtb.com"

class XTBClient:
    def __init__(self):
        self.session = requests.Session()
        self.stream_session = None
        self.sid = None

    def login(self):
        payload = {
            "command": "login",
            "arguments": {
                "userId": os.getenv("XTB_USERNAME"),
                "password": os.getenv("XTB_PASSWORD")
            }
        }
        res = self.session.post(f"{XTB_API_URL}/login", json=payload)
        if res.ok and res.json().get("status"):
            self.sid = res.json()["streamSessionId"]
            print("✅ Logged into XTB")
            return True
        print("❌ XTB login failed")
        return False

    def get_candles(self, symbol="EURUSD", timeframe="H1", limit=200):
        tf_map = {
            "M1": 1, "M5": 5, "M15": 15, "M30": 30,
            "H1": 60, "H4": 240, "D1": 1440
        }
        if timeframe not in tf_map:
            raise ValueError("Unsupported timeframe.")

        payload = {
            "command": "getChartLastRequest",
            "arguments": {
                "info": {
                    "period": tf_map[timeframe],
                    "start": 0,
                    "symbol": symbol
                }
            }
        }
        res = self.session.post(f"{XTB_API_URL}/getChartLastRequest", json=payload)
        if not res.ok or not res.json().get("status"):
            print("❌ Failed to fetch candles")
            return pd.DataFrame()

        candles = res.json()["returnData"]["rateInfos"]
        df = pd.DataFrame(candles)
        df["timestamp"] = pd.to_datetime(df["ctm"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df.rename(columns={"open": "open", "close": "close", "high": "high", "low": "low", "vol": "volume"}, inplace=True)
        return df[["open", "high", "low", "close", "volume"]].tail(limit)

    def logout(self):
        self.session.post(f"{XTB_API_URL}/logout")
        print("🔌 Logged out from XTB")

def get_xtb_data(symbol="EURUSD", timeframe="H1", limit=200):
    client = XTBClient()
    if client.login():
        df = client.get_candles(symbol, timeframe, limit)
        client.logout()
        return df
    return pd.DataFrame()
