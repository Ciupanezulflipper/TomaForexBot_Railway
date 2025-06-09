import asyncio
from core.signal_fusion import run_fused_analysis


async def run_full_fused_scan():
    """Wrapper to run fused analysis and return high-confidence signals."""
    print("[FUSED SCAN] Running fused analysis...")
    try:
        results = await run_fused_analysis()
        strong_signals = []

        for entry in results:
            if entry["final_score"] >= 6:
                strong_signals.append(entry)

        print(f"[FUSED SCAN] Found {len(strong_signals)} strong signals.")
        return strong_signals

    except Exception as e:
        print(f"[FUSED SCAN ERROR] {e}")
        return []
