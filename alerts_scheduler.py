# alerts_scheduler.py

import time
import asyncio
from datetime import datetime
from news_feeds import analyze_all_feeds    # News headline + logic scanner
from patterns_module import check_patterns  # Chart pattern checker (your main pairs)
from telegramsender import send_telegram_message

# Confirmation filters (can be extended)
from botstrategies import check_ema_crossover, check_rsi_zone, check_volume_spike

# List of core symbols
CORE_PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "US30"]
ALERT_THRESHOLD = 2  # Number of confirmations needed to trigger an alert

# Helper to check all confirmations
def is_confirmed(pattern_result, ema, rsi, volume, news_bias):
    confirmations = []
    if pattern_result: confirmations.append("pattern")
    if ema:            confirmations.append("ema")
    if rsi:            confirmations.append("rsi")
    if volume:         confirmations.append("volume")
    if news_bias:      confirmations.append("news")
    return len(confirmations) >= ALERT_THRESHOLD, confirmations

async def run_alerts_scheduler():
    print(f"[ALERTS] Scheduler started at {datetime.now()}")
    while True:
        # 1. News analysis (all feeds)
        news_alerts, _ = analyze_all_feeds()
        print(f"[ALERTS] News scan complete. Found {len(news_alerts)} signals.")

        # 2. Chart pattern and confirmation loop
        for symbol in CORE_PAIRS:
            print(f"[ALERTS] Checking {symbol} for signals...")
            pattern = check_patterns(symbol)
            ema = check_ema_crossover(symbol)
            rsi = check_rsi_zone(symbol)
            volume = check_volume_spike(symbol)
            news = any(alert['asset'] == symbol and alert['signal'] == 'BUY' for alert in news_alerts)

            is_ok, confirmations = is_confirmed(pattern, ema, rsi, volume, news)
            if is_ok:
                msg = (
                    f"🚨 ALERT: {symbol}\n"
                    f"Pattern: {pattern}\n"
                    f"EMA: {ema}, RSI: {rsi}, Volume: {volume}, News: {news}\n"
                    f"Confirmations: {', '.join(confirmations)}\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                await send_telegram_message(msg)
                print(f"[ALERTS] Sent alert for {symbol}: {msg}")
            else:
                print(f"[ALERTS] No strong setup for {symbol} ({confirmations})")
        # Wait for 10 minutes before next scan
        await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(run_alerts_scheduler())
