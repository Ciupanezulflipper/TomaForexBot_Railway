# TomaForexBot/marketdata.py

import time
import threading
import pandas as pd
import websocket
import json
import os

from dotenv import load_dotenv
load_dotenv()

XTB_USER = os.getenv("XTB_USER")
XTB_PASS = os.getenv("XTB_PASS")
XTB_DEMO = True  # Set to False for real account

class XTBConnector:
    def __init__(self):
        self.session_id = None
        self.ws = None
        self.data = {}

    def connect(self):
        url = "wss://ws.xtb.com/demo" if XTB_DEMO else "wss://ws.xtb.com/real"
        self.ws = websocket.WebSocket()
        self.ws.connect(url)

        login_payload = {
            "command": "login",
            "arguments": {
                "userId": XTB_USER,
                "password": XTB_PASS
            }
        }
        self.ws.send(json.dumps(login_payload))
        response = json.loads(self.ws.recv())
        if response["status"] is True:
            self.session_id = response["streamSessionId"]
            return True
        return False

    def get_candles(self, symbol="EURUSD", timeframe="H1", limit=200):
        candle_request = {
            "command": "getChartLastRequest",
            "arguments": {
                "info": {
                    "period": 60,
                    "start": int(time.time()) - (limit * 3600),
                    "symbol": symbol
                }
            }
        }
        self.ws.send(json.dumps(candle_request))
        response = json.loads(self.ws.recv())
        candles = response["returnData"]["rateInfos"]

        ohlc = {
            "time": [pd.to_datetime(c["ctm"], unit="ms") for c in candles],
            "open": [c["open"] for c in candles],
            "high": [c["high"] for c in candles],
            "low": [c["low"] for c in candles],
            "close": [c["close"] for c in candles],
            "volume": [c["vol"] for c in candles]
        }
        df = pd.DataFrame(ohlc)
        df.set_index("time", inplace=True)
        return df

# Global for other modules
xtb = XTBConnector()
def get_xtb_data(symbol="EURUSD", timeframe="H1", bars=200):
    if not xtb.connect():
        print("❌ XTB connection failed.")
        return pd.DataFrame()
    return xtb.get_candles(symbol=symbol, timeframe=timeframe, limit=bars)
get_mt5_data = get_xtb_data
get_ohlc = get_xtb_data

