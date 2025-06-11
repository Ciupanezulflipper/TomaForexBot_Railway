import logging
from indicators import calculate_ema, calculate_rsi
from patterns import detect_patterns
from marketdata import get_ohlc
from fibonacci import get_fibonacci_levels
from weights_config import get_weights
from riskanalysis import evaluate_risk_zone
from core.signal_utils import calculate_signal_score

logger = logging.getLogger(__name__)

async def generate_trade_decision(symbol, chat_id=None, test_only=False):
    try:
        tf_list = ['H1', 'H4', 'D1']
        results = []

        for tf in tf_list:
            df = await get_ohlc(symbol, tf, bars=150)
            if df is None or df.empty:
                continue

            df.name = f"{symbol}_{tf}"
            df["ema9"] = calculate_ema(df["close"], 9)
            df["ema21"] = calculate_ema(df["close"], 21)
            ema_signal = df["ema9"].iloc[-1] > df["ema21"].iloc[-1]

            rsi_value = calculate_rsi(df["close"])
            patterns = detect_patterns(df)

            last_price = df["close"].iloc[-1]
            fib = get_fibonacci_levels(last_price)
            risk_zone = evaluate_risk_zone(last_price, fib)

            pattern_score = len(patterns)
            ema_score = 1 if ema_signal else 0
            rsi_score = 1 if (rsi_value < 30 or rsi_value > 70) else 0
            fib_score = fib.get("score", 0)
            risk_score = 1 if risk_zone == "safe" else 0

            frame_score = calculate_signal_score(rsi_score, pattern_score, ema_score, fib_score, risk_score)
            signal = "BUY" if ema_signal and rsi_value < 30 else "SELL" if not ema_signal and rsi_value > 70 else "WAIT"

            results.append({
                "tf": tf,
                "score": frame_score,
                "signal": signal,
                "rsi": rsi_value,
                "ema": f"{df['ema9'].iloc[-1]:.4f} > {df['ema21'].iloc[-1]:.4f}" if ema_signal else f"{df['ema9'].iloc[-1]:.4f} < {df['ema21'].iloc[-1]:.4f}",
                "patterns": patterns,
                "fib": fib,
                "risk": risk_zone,
            })

        if not results:
            return {"confirmed": False, "signal": "WAIT", "reason": "No valid timeframe data."}

        buy_count = sum(1 for r in results if r["signal"] == "BUY")
        sell_count = sum(1 for r in results if r["signal"] == "SELL")
        final_signal = "BUY" if buy_count >= 2 else "SELL" if sell_count >= 2 else "WAIT"
        avg_score = sum(r["score"] for r in results) / len(results)
        confirmed = avg_score >= 4 and final_signal in ["BUY", "SELL"]

        return {
            "confirmed": confirmed,
            "signal": final_signal,
            "avg_score": avg_score,
            "reason": f"{buy_count} BUY vs {sell_count} SELL from {len(results)} timeframes",
            "details": results
        }

    except Exception as e:
        logger.error(f"[generate_trade_decision] Error for {symbol}: {e}")
        return {"confirmed": False, "signal": "WAIT", "reason": str(e)}
