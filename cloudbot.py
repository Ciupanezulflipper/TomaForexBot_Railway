from dotenv import load_dotenv
import os
import pandas as pd
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

def get_scalar(val):
    # Handles Series and scalars robustly
    if isinstance(val, pd.Series):
        return float(val.iloc[0])
    return float(val)

def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_fibonacci_levels(series):
    # Handles Series-of-Series edge cases (pandas/yfinance future-proof)
    hi = series.max()
    lo = series.min()
    if isinstance(hi, pd.Series): hi = hi.iloc[0]
    if isinstance(lo, pd.Series): lo = lo.iloc[0]
    highest = float(hi)
    lowest = float(lo)
    diff = highest - lowest
    levels = {
        "61.8%": highest - 0.618 * diff,
        "50.0%": highest - 0.500 * diff,
        "38.2%": highest - 0.382 * diff,
    }
    return levels, highest, lowest

def detect_bullish_engulfing(df):
    if len(df) < 2:
        return False
    prev = df.iloc[-2]
    curr = df.iloc[-1]
    prev_open = get_scalar(prev['Open'])
    prev_close = get_scalar(prev['Close'])
    curr_open = get_scalar(curr['Open'])
    curr_close = get_scalar(curr['Close'])
    prev_body = abs(prev_close - prev_open)
    curr_body = abs(curr_close - curr_open)
    return (
        prev_close < prev_open and
        curr_close > curr_open and
        curr_body > prev_body and
        curr_open < prev_close and
        curr_close > prev_open
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Cloud bot online. Telegram working!")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pong! I am online.")

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Usage: /analyze SYMBOL (e.g. /analyze EURUSD)")
            return
        symbol = context.args[0]
        if symbol.upper() == "EURUSD":
            ticker = "EURUSD=X"
        elif symbol.upper() == "GBPUSD":
            ticker = "GBPUSD=X"
        else:
            ticker = symbol + "=X"

        df = yf.download(ticker, period="2mo", interval="1h")
        if df.empty:
            await update.message.reply_text(f"No data found for {symbol}.")
            return

        close = df['Close']
        ema9 = calculate_ema(close, 9)
        ema21 = calculate_ema(close, 21)
        rsi14 = calculate_rsi(close, 14)
        fib_levels, swing_high, swing_low = get_fibonacci_levels(close.tail(50))

        last_price = get_scalar(close.iloc[-1])
        last_ema9 = get_scalar(ema9.iloc[-1])
        last_ema21 = get_scalar(ema21.iloc[-1])
        last_rsi = get_scalar(rsi14.iloc[-1])
        bullish_engulf = detect_bullish_engulfing(df.tail(3))
        pattern_str = "Bullish Engulfing" if bullish_engulf else "No strong pattern"
        bullish_count = 0
        if last_ema9 > last_ema21: bullish_count += 1
        if last_rsi > 50: bullish_count += 1
        if bullish_engulf: bullish_count += 1
        if bullish_count >= 2:
            signal = "BUY ✅"
        elif bullish_count == 1:
            signal = "NEUTRAL ⚪"
        else:
            signal = "SELL ❌"
        message = (
            f"Analysis for {symbol}:\n"
            f"Price: {last_price:.5f}\n"
            f"EMA9: {last_ema9:.5f}\n"
            f"EMA21: {last_ema21:.5f}\n"
            f"RSI(14): {last_rsi:.2f}\n"
            f"Pattern: {pattern_str}\n"
            f"\nFibonacci Levels (last 50 H1):\n"
            f"High: {swing_high:.5f} / Low: {swing_low:.5f}\n"
            f"61.8%: {fib_levels['61.8%']:.5f}\n"
            f"50.0%: {fib_levels['50.0%']:.5f}\n"
            f"38.2%: {fib_levels['38.2%']:.5f}\n"
            f"\nSignal: {signal}"
        )
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("analyze", analyze))
    app.run_polling()
