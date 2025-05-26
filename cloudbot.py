import os
import pandas as pd
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

def get_scalar(val):
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

def get_atr(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def get_adx(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    up_move = high.diff()
    down_move = low.diff(-1)
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = (-down_move).where((down_move > up_move) & (down_move > 0), 0.0)
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    tr14 = tr.rolling(period).sum()
    plus_di = 100 * plus_dm.rolling(period).sum() / tr14
    minus_di = 100 * minus_dm.rolling(period).sum() / tr14
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(period).mean()
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
    prev_open = get_scalar(prev['Open'])
    prev_close = get_scalar(prev['Close'])
    curr_open = get_scalar(curr['Open'])
    curr_close = get_scalar(curr['Close'])
    prev_body = abs(prev_close - prev_open)
    curr_body = abs(curr_close - curr_open)
    return (
        (prev_close < prev_open) and
        (curr_close > curr_open) and
        (curr_body > prev_body) and
        (curr_open < prev_close) and
        (curr_close > prev_open)
    )

def candle_body_gt_50(df):
    if len(df) < 1:
        return False
    curr = df.iloc[-1]
    open_ = get_scalar(curr['Open'])
    close = get_scalar(curr['Close'])
    high = get_scalar(curr['High'])
    low = get_scalar(curr['Low'])
    body = abs(close - open_)
    rng = high - low
    return body > 0.5 * rng if rng else False

def bullish_stack(df):
    if len(df) < 1:
        return False
    curr = df.iloc[-1]
    close = get_scalar(curr['Close'])
    ema9 = calculate_ema(df['Close'], 9).iloc[-1]
    ema21 = calculate_ema(df['Close'], 21).iloc[-1]
    return close > ema9 > ema21

def bearish_stack(df):
    if len(df) < 1:
        return False
    curr = df.iloc[-1]
    close = get_scalar(curr['Close'])
    ema9 = calculate_ema(df['Close'], 9).iloc[-1]
    ema21 = calculate_ema(df['Close'], 21).iloc[-1]
    return close < ema9 < ema21

def check_previous_candle_bullish(df):
    if len(df) < 2:
        return False
    prev = df.iloc[-2]
    open_ = get_scalar(prev['Open'])
    close = get_scalar(prev['Close'])
    return close > open_

def check_previous_candle_bearish(df):
    if len(df) < 2:
        return False
    prev = df.iloc[-2]
    open_ = get_scalar(prev['Open'])
    close = get_scalar(prev['Close'])
    return close < open_

def price_near_fib(price, fib_levels, threshold=0.0005):
    for lvl in fib_levels.values():
        if abs(price - lvl) <= threshold:
            return True
    return False

def support_resistance_near(price, swing_high, swing_low, threshold=0.0005):
    return abs(price - swing_high) <= threshold or abs(price - swing_low) <= threshold

def volume_spike(df, period=20, spike_mult=1.5):
    if 'Volume' not in df.columns or len(df) < period+1:
        return False
    avg = df['Volume'].tail(period+1)[:-1].mean()
    curr = df['Volume'].iloc[-1]
    return curr > spike_mult * avg

def rsi_divergence(df, rsi):
    if len(df) < 2:
        return False
    price_diff = df['Close'].iloc[-1] - df['Close'].iloc[-2]
    rsi_diff = rsi.iloc[-1] - rsi.iloc[-2]
    return (price_diff > 0 and rsi_diff < 0) or (price_diff < 0 and rsi_diff > 0)

TOKEN = os.getenv("TELEGRAM_TOKEN")

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
        atr14 = get_atr(df, 14)
        adx14 = get_adx(df, 14)
        fib_levels, swing_high, swing_low = get_fibonacci_levels(close.tail(50))
        last_price = get_scalar(close.iloc[-1])
        last_ema9 = get_scalar(ema9.iloc[-1])
        last_ema21 = get_scalar(ema21.iloc[-1])
        last_rsi = get_scalar(rsi14.iloc[-1])
        last_atr = get_scalar(atr14.iloc[-1])
        last_adx = get_scalar(adx14.iloc[-1])

        bullish_engulf = detect_bullish_engulfing(df.tail(3))
        body_50 = candle_body_gt_50(df)
        bull_stack = bullish_stack(df)
        bear_stack = bearish_stack(df)
        prev_bull = check_previous_candle_bullish(df)
        prev_bear = check_previous_candle_bearish(df)
        fib_near = price_near_fib(last_price, fib_levels)
        sr_near = support_resistance_near(last_price, swing_high, swing_low)
        vol_spike = volume_spike(df)
        rsi_div = rsi_divergence(df, rsi14)

        score = sum([
            last_ema9 > last_ema21,
            last_rsi > 55 or last_rsi < 45,
            bullish_engulf,
            body_50,
            last_atr > 0,
            last_adx > 20,
            bull_stack or bear_stack,
            prev_bull or prev_bear,
            fib_near,
            sr_near,
            not (45 < last_rsi < 55),
            vol_spike,
            not rsi_div,
            True,  # multi-frame placeholder
        ])

        auto_checks = [
            f"EMA9: {last_ema9:.3f} > EMA21: {last_ema21:.3f} = {last_ema9 > last_ema21}",
            f"RSI(14): {last_rsi:.2f}",
            f"Bullish Engulfing: {bullish_engulf}",
            f"Candle Body > 50%: {body_50}",
            f"ATR14: {last_atr:.5f}",
            f"ADX14: {last_adx:.2f}",
            f"Stack (Close>EMA9>EMA21): {bull_stack}",
            f"Previous Candle Confirms: Bullish? {prev_bull} Bearish? {prev_bear}",
            f"Price near Fib: {fib_near}",
            f"Support/Resistance near: {sr_near}",
            f"Volume Spike: {vol_spike}",
            f"RSI Divergence: {rsi_div}",
        ]

        message = (
            f"Analysis for {symbol}:\n"
            f"Price: {last_price:.3f}\n"
            f"\n" + "\n".join(auto_checks) + "\n"
            f"\nFibonacci Levels (last 50 H1):\n"
            f"High: {swing_high:.3f} / Low: {swing_low:.3f}\n"
            f"61.8%: {fib_levels['61.8%']:.3f}\n"
            f"50.0%: {fib_levels['50.0%']:.3f}\n"
            f"38.2%: {fib_levels['38.2%']:.3f}\n"
            f"\nSignal Score: {score}/16\n"
            f"\n---MANUAL CHECKS---\n"
            f"- Check spread (avoid wide spread)\n"
            f"- Check news/economic calendar (no red event)\n"
            f"- Check sentiment (forums, groups, X)\n"
            f"- Set SL/TP at logical technical levels\n"
            f"- Visually confirm chart before entering trade\n"
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
