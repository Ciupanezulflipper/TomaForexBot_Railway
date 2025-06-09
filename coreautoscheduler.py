import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from core.signal_fusion import run_fused_analysis
from core.telegramalert import send_fused_alerts


async def check_and_alert():
    print(f"[AUTO] Running fused analysis at {datetime.utcnow().strftime('%H:%M UTC')}")
    try:
        fused_signals = await run_fused_analysis()
        await send_fused_alerts(fused_signals)
    except Exception as e:
        print(f"[AUTO ERROR] {e}")


def start_auto_alerts():
    scheduler = AsyncIOScheduler(timezone="UTC")

    # Schedule before market sessions open
    scheduler.add_job(check_and_alert, trigger='cron', hour=6, minute=50)   # London Open (approx)
    scheduler.add_job(check_and_alert, trigger='cron', hour=12, minute=50)  # US Open (approx)

    # Optional: add another scan in the evening for big reversals
    scheduler.add_job(check_and_alert, trigger='cron', hour=20, minute=30)

    print("✅ Auto-alert scheduler started.")
    scheduler.start()
