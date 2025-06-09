def should_alert(signal_dict: dict, sentiment: str) -> bool:
    """
    Check if both the technical signal and sentiment agree.
    """
    if not signal_dict or not sentiment:
        return False

    if signal_dict.get("signal") == "BUY" and sentiment == "BULLISH":
        return True
    if signal_dict.get("signal") == "SELL" and sentiment == "BEARISH":
        return True
    return False


def build_alert_message(symbol: str, tf: str, signal: str, entry: float, sl: float, tp: float, atr_pips: int, reason: str, timestamp: str) -> str:
    """
    Create a formatted alert message.
    """
    return (
        f"📢 <b>Auto Signal Alert</b>\n"
        f"Symbol: <b>{symbol}</b> | TF: <b>{tf}</b>\n"
        f"Signal: <b>{signal}</b>\n"
        f"Entry: {entry:.5f}\n"
        f"SL: {sl:.5f} | TP: {tp:.5f}\n"
        f"ATR: {atr_pips} pips\n"
        f"Reason: {reason}\n"
        f"Time: {timestamp} UTC"
    )
