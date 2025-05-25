import os
import time
import json
import pandas as pd
import websocket
from dotenv import load_dotenv

load_dotenv()

XTB_USER = os.getenv("XTB_USER")
XTB_PASS = os.getenv("XTB_PASS")
XTB_DEMO = os.getenv("XTB_DEMO", "true").lower() == "true"


class XTBConnector:
    def __init__(self):
        self.ws = None
        self.session_id = None
        self.connected = False

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
                self.session_id = response.get("streamSessionId")
                self.connected = True
                print("✅ Connected to XTB")
                return True
            else:
                print("❌ Login failed:", response)
                return False
        except Exception as e:
            print(f"❌ XTB connection error: {e}")
            self.connected = False
            return False

    def ping(self):
        try:
            self.ws.send(json.dumps({"command": "ping"}))
            pong = self.ws.recv()
            return True
        except:
            return False

    def get_candles(self, symbol="EURUSD", timeframe="H1", limit=200):
        if not self.connected and not self.connect():
            return pd.DataFrame()

        try:
            self.ws.send(json.dumps({
                "command": "getChartLastRequest",
                "arguments": {
                    "info": {
                        "period": 60,  # H1 = 60 min
                        "start": int(time.time()) - (limit * 3600),
                        "symbol": symbol
                    }
                }
            }))
            response = json.loads(self.ws.recv())
            if "returnData" not in response or "rateInfos" not in response["returnData"]:
                print(f"⚠️ XTB response missing data for {symbol}")
                return pd.DataFrame()

            candles = response["returnData"]["rateInfos"]
            df = pd.DataFrame({
                "time": [pd.to_datetime(c["ctm"], unit="ms") for c in candles],
                "open": [c["open"] for c in candles],
                "high": [c["high"] for c in candles],
                "low": [c["low"] for c in candles],
                "close": [c["close"] for c in candles],
                "volume": [c["vol"] for c in candles],
            }).set_index("time")

            return df

        except Exception as e:
            print(f"❌ Failed to fetch candles from XTB: {e}")
            return pd.DataFrame()


xtb = XTBConnector()
