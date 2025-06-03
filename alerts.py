# alerts.py
import time

ALERT_LEVELS = {
    "info": "ℹ️",
    "warning": "⚠️",
    "critical": "❗"
}

alert_history = {}  # (symbol, level): last_alert_time

def should_alert(symbol, level, throttle_seconds=300):
    now = time.time()
    key = (symbol, level)
    last = alert_history.get(key, 0)
    if now - last > throttle_seconds:
        alert_history[key] = now
        return True
    return False

def build_alert_message(symbol, signal, level, explanation="", chart_url=None):
    emoji = ALERT_LEVELS.get(level, "🔔")
    msg = f"{emoji} [{symbol}] {level.upper()} ALERT: {signal}\n"
    if explanation:
        msg += f"Details: {explanation}\n"
    if chart_url:
        msg += f"[Chart Link]({chart_url})"
    return msg
