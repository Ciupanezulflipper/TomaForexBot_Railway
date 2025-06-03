# patterns_alerts_auto.py
import asyncio
import time
from patterns_alerts import analyze_and_alert

CHECK_INTERVAL = 60 * 15  # 15 min

if __name__ == "__main__":
    print("[PATTERN ALERTS AUTO] Starting loop. Ctrl+C to stop.")
    while True:
        try:
            asyncio.run(analyze_and_alert())
        except Exception as e:
            print(f"[AUTO ERROR] {e}")
        time.sleep(CHECK_INTERVAL)
