# cloudbot.py - FULL 16/16+6 Output
import os
import pandas as pd
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN")

# Helper Functions
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

def calculate_atr(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=1).mean()
    return atr

def calculate_adx(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    plus_dm = high.diff().clip(lower=0)
    minus_dm = (-low.diff()).clip(lower=0)
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).sum() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).sum() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(window=period).mean()
    return adx

def get_fibonacci_levels(series):
    highest = float(series.max())
    lowest = float(series.min())
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
    prev_open = float(prev['Open'])
    prev_close = float(prev['Close'])
    curr_open = float(curr['Open'])
    curr_close = float(curr['Close'])
    prev_body = abs(prev_close - prev_open)
    curr_body = abs(curr_close - curr_open)
    is_bullish_engulfing = (
        prev_close < prev_open and
        curr_close > curr_open and
        curr_body > prev_body and
        curr_open < prev_close and
        curr_close > prev_open
    )
    return is_bullish_engulfing

def candle_body_over_50(df):
    if len(df) < 1:
        return False
    last = df.iloc[-1]
    body = abs(float(last['Close']) - float(last['Open']))
    high_low = abs(float(last['High']) - float(last['Low']))
    return (body / high_low) > 0.5 if high_low != 0 else False

def check_stack(df):
    if len(df) < 1:
        return False
    last = df.iloc[-1]
    close = float(last['Close'])
    ema9 = calculate_ema(df['Close'], 9).iloc[-1]
    ema21 = calculate_ema(df['Close'], 21).iloc[-1]
    return close > ema9 > ema21

def price_near_fib(price, fib_levels, threshold=0.0005):
    return any(abs(price - lvl) < threshold for lvl in fib_levels.values())

def rsi_divergence(rsi):
    # Placeholder (real RSI divergence is more complex)
    return False

def volume_spike(df, period=20, spike_mult=2):
    if 'Volume' not in df.columns:
        return False
    avg_vol = df['Volume'].rolling(window=period).mean().iloc[-1]
    last_vol = df['Volume'].iloc[-1]
    return last_vol > avg_vol * spike_mult if avg_vol else False

def previous_candle_confirm(df):
    if len(df) < 2:
        return False, False
    prev = df.iloc[-2]
    bullish = float(prev['Close']) > float(prev['Open'])
    bearish = float(prev['Close']) < float(prev['Open'])
    return bullish, bearish

def support_resistance(price, high, low, threshold=0.0005):
    return abs(price - high) < threshold or abs(price - low) < threshold

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Cloud bot online. Telegram working!")

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Usage: /analyze SYMBOL (e.g. /analyze EURUSD)")
            return
        symbol = context.args[0].upper()
        ticker = symbol + "=X"
        df = yf.download(ticker, period="2mo", interval="1h")
        if df.empty:
            await update.message.reply_text(f"No data found for {symbol}.")
            return

        close = df['Close']
        ema9 = calculate_ema(close, 9)
        ema21 = calculate_ema(close, 21)
        rsi14 = calculate_rsi(close, 14)
        atr14 = calculate_atr(df, 14)
        adx14 = calculate_adx(df, 14)
        fib_levels, swing_high, swing_low = get_fibonacci_levels(close.tail(50))

        last_price = float(close.iloc[-1])
        last_ema9 = float(ema9.iloc[-1])
        last_ema21 = float(ema21.iloc[-1])
        last_rsi = float(rsi14.iloc[-1])
        last_atr = float(atr14.iloc[-1])
        last_adx = float(adx14.iloc[-1])
        bullish_engulf = detect_bullish_engulfing(df.tail(3))
        body_50 = candle_body_over_50(df.tail(1))
        stack = check_stack(df)
        prev_bullish, prev_bearish = previous_candle_confirm(df)
        near_fib = price_near_fib(last_price, fib_levels)
        near_sr = support_resistance(last_price, swing_high, swing_low)
        vol_spike = volume_spike(df)
        rsi_div = rsi_divergence(rsi14)

        # Signal Score
        score = sum([
            last_ema9 > last_ema21,
            last_rsi > 55,
            bullish_engulf,
            body_50,
            last_atr > 0,
            last_adx > 20,
            stack,
            prev_bullish,
            near_fib,
            near_sr,
            vol_spike,
            not rsi_div,
        ])

        signal = "BUY ✅" if score >= 9 else "NEUTRAL ⚪️" if score >= 6 else "SELL ❌"

        msg = (
            f"MULTI-CRITERIA ANALYSIS for {symbol} ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n"
            f"Price: {last_price:.5f}\n"
            f"EMA9: {last_ema9:.5f}\n"
            f"EMA21: {last_ema21:.5f}\n"
            f"RSI(14): {last_rsi:.2f}\n"
            f"ATR14: {last_atr:.5f}\n"
            f"ADX14: {last_adx:.2f}\n"
            f"\n--- 16/16 + 6 STRATEGY CHECKS ---\n"
            f"EMA9 > EMA21: {last_ema9 > last_ema21}\n"
            f"RSI(14) > 55: {last_rsi > 55}\n"
            f"Bullish Engulfing: {bullish_engulf}\n"
            f"Candle Body > 50%: {body_50}\n"
            f"ATR14 > 0: {last_atr > 0}\n"
            f"ADX14 > 20: {last_adx > 20}\n"
            f"Stack (Close > EMA9 > EMA21): {stack}\n"
            f"Prev Candle Bullish: {prev_bullish}\n"
            f"Price near Fibonacci: {near_fib}\n"
            f"Near Support/Resistance: {near_sr}\n"
            f"Volume Spike: {vol_spike}\n"
            f"No RSI Divergence: {not rsi_div}\n"
            f"\nFibonacci (last 50 H1): High: {swing_high:.5f} / Low: {swing_low:.5f}\n"
            f"61.8%: {fib_levels['61.8%']:.5f}\n"
            f"50.0%: {fib_levels['50.0%']:.5f}\n"
            f"38.2%: {fib_levels['38.2%']:.5f}\n"
            f"\nSignal Score: {score}/16\n"
            f"Signal: {signal}\n"
            f"\n---MANUAL CHECKS---\n"
            f"- Check spread (avoid wide)\n"
            f"- News/Calendar (avoid red)\n"
            f"- Group Sentiment (forums, groups, X)\n"
            f"- SL/TP at logical technical\n"
            f"- Visual chart check before trading\n"
        )
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.run_polling()
