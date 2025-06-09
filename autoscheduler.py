import asyncio
import datetime
import pytz
from telegramalert import send_alert_message
from core.signal_fusion import run_fused_analysis

# Set your preferred timezone (example: Europe/Bucharest)
LOCAL_TZ = pytz.timezone("Europe/Bucharest")

# Define target hours for market opens (UTC)
SCHEDULE = {
    "London Open": datetime.time(hour=7, minute=0),   # 9:00 Bucharest
    "US Open": datetime.time(hour=13, minute=30),     # 16:30 Bucharest
    "Midday Check": datetime.time(hour=11, minute=0), # 14:00 Bucharest
}

ALERT_THRESHOLD = 6  # Minimum final score to trigger alert

def should_run_now(now_utc):
    """Check if current time is close to any scheduled alert."""
    for label, sched_time in SCHEDULE.items():
        sched_dt = datetime.datetime.combine(now_utc.date(), sched_time, tzinfo=pytz.UTC)
        diff = abs((now_utc - sched_dt).total_seconds())
        if diff < 60:  # within 1 minute
            return label
    return None

async def run_auto_alert():
    while True:
        now_utc = datetime.datetime.now(pytz.UTC)
        label = should_run_now(now_utc)

        if label:
            print(f"⏰ Triggering scan for: {label}")
            try:
                fused_signals = await run_fused_analysis()
                if not fused_signals:
                    print("⚠️ No trades found.")
                    await asyncio.sleep(60)
                    continue

                for signal in fused_signals:
                    if signal["final_score"] >= ALERT_THRESHOLD:
                        msg = (
                            f"🚨 *{label} Alert*\n\n"
                            f"*{signal['pair']}* `{signal['type']}`\n"
                            f"Entry: `{signal['entry_price']}` | Live: `{signal['current_price']}`\n"
                            f"🧠 Strategy Score: *{signal['strategy_score']}* → Final: *{signal['final_score']}*\n"
                            f"🗞️ News: {signal['news_comment']}\n"
                        )
                        send_alert_message(msg)
            except Exception as e:
                print(f"❌ Auto-alert error: {str(e)}")

        await asyncio.sleep(60)  # Check every minute
