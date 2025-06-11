# 16in16_MultiFrame_Strat.py

import asyncio
from analysis_engine import analyze_symbol_multi_tf
from news_signal_logic import analyze_multiple_headlines

# Dummy headlines for testing (replace with live headlines later)
recent_headlines = [
    "Interest rate hike expected by ECB",
    "Tariff delay announced by U.S.",
    "Stimulus package proposed in Europe"
]

async def generate_trade_decision(symbol):
    print(f"🔍 Running 16/16 Multi-Frame Strategy for {symbol}...")

    result = await analyze_symbol_multi_tf(symbol)
    if not result["confirmed"]:
        return f"⚠️ No strong signal for {symbol}.\nReason: {result['reason']}"

    # Combine with news signal
    news_result = analyze_multiple_headlines(recent_headlines, symbol)
    news_score = news_result["score"]
    news_reason = news_result["reasons"]

    # Add news_score to the final avg_score
    total_score = result["avg_score"] + news_score
    final_signal = result["signal"]

    # Adjust final signal if news strongly disagrees
    if news_score >= 2 and final_signal == "SELL":
        final_signal = "WAIT ❗ (conflict: bullish news)"
    elif news_score <= -2 and final_signal == "BUY":
        final_signal = "WAIT ❗ (conflict: bearish news)"

    summary = f"📊 16/16 Strategy for {symbol}\n"
    summary += f"Signal: {final_signal}\n"
    summary += f"Technical Avg Score: {result['avg_score']:.2f}\n"
    summary += f"News Score: {news_score} ({'; '.join(news_reason) if news_reason else 'No matching news'})\n"
    summary += f"{result['reason']}\n\n"

    for r in result["details"]:
        summary += (
            f"🕒 {r['tf']}: {r['signal']} (Score: {r['score']:.1f})\n"
            f"EMA: {r['ema']} | RSI: {r['rsi']:.1f}\n"
            f"Pattern(s): {r['patterns']}\n"
            f"Fib: {r['fib']}\n"
            f"Risk: {r['risk']}\n"
            "----------------------\n"
        )

    summary += (
        "\nMANUAL CHECKS (recommended):\n"
        "- [ ] Spread/Commission OK for entry?\n"
        "- [ ] Group/Forum Sentiment or warnings\n"
        "- [ ] Check actual chart\n"
        "\n🧠 Final Decision: Proceed if all checks align.\n"
    )

    return summary


if __name__ == "__main__":
    symbol = "EURUSD"  # test pair
    output = asyncio.run(generate_trade_decision(symbol))
    print(output)
