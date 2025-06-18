import os
import logging
from dotenv import load_dotenv
import requests

load_dotenv()
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_API_SECRET = os.getenv('ALPACA_API_SECRET')
ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

def place_alpaca_order(symbol, side, qty, order_type="market", time_in_force="gtc"):
    logger = logging.getLogger(__name__)
    url = f"{ALPACA_BASE_URL}/v2/orders"
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_API_SECRET
    }
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side.lower(),
        "type": order_type,
        "time_in_force": time_in_force
    }
    try:
        r = requests.post(url, json=data, headers=headers)
        r.raise_for_status()
        logger.info(f"Order placed: {r.json()}")
        return r.json()
    except Exception as e:
        logger.error(f"Alpaca order failed: {e}")
        return None