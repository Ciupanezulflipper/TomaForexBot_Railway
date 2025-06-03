import time
from news_feeds import analyze_all_feeds
from pattern_alerts import analyze_patterns_for_all
from economic_calendar_module import check_upcoming_events
from telegramsender import send_telegram_message

# Settings
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "US30"]
INTERVAL = 60 * 15  # 15 min

def combine_signals(news_signals, pattern_signals):
    combined_alerts = []
    for asset in PAIRS:
        news_signal = next((s for s in news_signals if s['asset'] == asset), None)
        pattern_signal = next((s for s in pattern_signals if s['asset'] == asset), None)

        if news_signal and pattern_signal:
            if news_signal['signal'] == pattern_signal['signal'] and news_signal['signal'] in ("BUY", "SELL"):
                alert = {
                    "asset": asset,
                    "signal": news_signal['signal'],
                    "reason": f"News: {news_signal.get('reason','')} | Pattern: {pattern_signal.get('reason','')}"
                }
                combined_alerts.append(alert)
    return combined_alerts

def multi_layer_loop():
    print("[MULTI-LAYER ALERT] Starting loop.")
    while True:
        try:
            print("[MULTI-LAYER] Checking news...")
            news_signals, _ = analyze_all_feeds()
            print("[MULTI-LAYER] Checking patterns...")
            pattern_signals = analyze_patterns_for_all()
            print("[MULTI-LAYER] Checking calendar events...")
            events = check_upcoming_events()
            
            alerts = combine_signals(news_signals, pattern_signals)
            for alert in alerts:
                msg = (
                    f"🚦 [MULTI-LAYER CONFIRMATION]\n"
                    f"Pair: {alert['asset']}\n"
                    f"Signal: {alert['signal']}\n"
                    f"Reason: {alert['reason']}\n"
                )
                if events:
                    msg += f"\nUpcoming events:\n{events}"
                send_telegram_message(msg)
            if not alerts:
                print("[MULTI-LAYER] No strong confluence trades at this time.")
        except Exception as e:
            print(f"[MULTI-LAYER ERROR] {e}")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    multi_layer_loop()
