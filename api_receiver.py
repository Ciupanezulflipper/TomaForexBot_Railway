from fastapi import FastAPI, Request
import pandas as pd
from marketdata import get_ohlc  # fallback if needed
from core.signal_fusion import generate_trade_decision

app = FastAPI()
DATA = {}  # hold latest uploaded data per symbol

@app.post("/api/receive_data")
async def receive_data(request: Request):
    body = await request.json()
    symbol = body.get("symbol")
    candles = body.get("data")

    if not symbol or not candles:
        return {"status": "error", "message": "Missing symbol or data"}

    df = pd.DataFrame(candles)
    df["datetime"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("datetime", inplace=True)
    
    # analyze it
    results = await generate_trade_decision(symbol)
    DATA[symbol] = results

    return {"status": "success", "symbol": symbol, "result": results}
