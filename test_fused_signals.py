from core_signal_fusion import evaluate_fused_signal

# ✅ Simulated technical signals (you can replace with real values from strategy)
test_signals = [
    {"pair": "EURUSD", "direction": "SELL", "score": 3},
    {"pair": "GBPUSD", "direction": "SELL", "score": 4},
    {"pair": "USDJPY", "direction": "BUY",  "score": 2},
    {"pair": "XAUUSD", "direction": "BUY",  "score": 5}
]

print("🔍 Running fused signal analysis...\n")

for signal in test_signals:
    pair = signal["pair"]
    direction = signal["direction"]
    base_score = signal["score"]

    final_score, comment = evaluate_fused_signal(pair, direction, base_score)

    print(f"📈 {pair} {direction} | Strategy Score: {base_score} → Final: {final_score}")
    print(f"💬 {comment}\n")
