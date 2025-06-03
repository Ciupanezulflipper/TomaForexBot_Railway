import os
import pandas as pd
import yfinance as yf
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- ACCESS CONTROL ---
# Only allow these Telegram user IDs
ALLOWED_USERS = [6074056245]  # Replace with your own Telegram user ID(s)

def is_allowed(update):
    return update.effective_user.id in ALLOWED_USERS

# --- STRATEGY FUNCTIONS ---
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
    atr = tr.rolling(window=period).mean()
    return atr

def get_adx(df, period=14):
    up = df['High'] - df['High'].shift(1)
    down = df['Low'].shift(1) - df['Low']
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    tr = pd.concat([
        df['High'] - df['Low'],
        (df['High'] - df['Close'].shift()).abs(),
        (df['Low'] - df['Close'].shift()).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).sum() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).sum() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(window=period).mean()
    try:
        val = adx.iloc[-1]
        if pd.isnull(val) or isinstance(val, pd.Series):
            return None
        return float(val)
    except Exception:
        return None

def get_fibonacci_levels(series):
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

def analyze_frame(df, timeframe):
    out = {}
    close = df['Close']
    ema9 = calculate_ema(close, 9)
    ema21 = calculate_ema(close, 21)
    rsi14 = calculate_rsi(close, 14)
    atr14 = get_atr(df, 14)
    adx14 = get_adx(df, 14) if len(df) > 30 else None
    out['ema9'] = get_scalar(ema9.iloc[-1])
    out['ema21'] = get_scalar(ema21.iloc[-1])
    out['rsi14'] = get_scalar(rsi14.iloc[-1])
    out['atr14'] = get_scalar(atr14.iloc[-1]) if not pd.isnull(atr14.iloc[-1]) else None
    out['adx14'] = adx14
    out['bullish_engulf'] = detect_bullish_engulfing(df.tail(3))
    last = df.iloc[-1]
    open_ = get_scalar(last['Open'])
    close_ = get_scalar(last['Close'])
    high_ = get_scalar(last['High'])
    low_ = get_scalar(last['Low'])
    body = abs(close_ - open_)
    rang = high_ - low_
    out['body_50'] = (body / rang) > 0.5 if rang > 0 else False
    return out

def multi_frame_analyze(symbol="EURUSD"):
    timeframes = {
        'H1': '1h',
        'H4': '4h',
        'D1': '1d'
    }
    results = {}
    agreement = []
    confirmations = {}
    for label, tf in timeframes.items():
        df = yf.download(f"{symbol}=X", period="3mo", interval=tf)
        if df.empty:
            results[label] = { 'direction': 'NO DATA', 'bullish_count': 0, 'bearish_count': 0, 'logic': [] }
            continue
        frame = analyze_frame(df, label)
        bull_count = 0
        bear_count = 0
        logic = []
        if frame['ema9'] > frame['ema21']:
            bull_count += 1; logic.append('EMA9>21')
        elif frame['ema9'] < frame['ema21']:
            bear_count += 1
        if frame['rsi14'] > 55:
            bull_count += 1; logic.append('RSI>55')
        elif frame['rsi14'] < 45:
            bear_count += 1
        if frame['bullish_engulf']:
            bull_count += 1; logic.append('BullEngulf')
        if frame['body_50']:
            bull_count += 1; logic.append('Body>50%')
        if frame['adx14'] and frame['adx14'] > 20:
            bull_count += 1; logic.append('ADX>20')
        confirmations[label] = bull_count
        direction = 'BUY' if bull_count >= 4 else ('SELL' if bear_count >= 2 else 'NEUTRAL')
        agreement.append(direction)
        results[label] = {
            'direction': direction,
            'bullish_count': bull_count,
            'bearish_count': bear_count,
            'ema9': frame['ema9'],
            'ema21': frame['ema21'],
            'rsi14': frame['rsi14'],
            'bullish_engulf': frame['bullish_engulf'],
            'body_50': frame['body_50'],
            'adx14': frame['adx14'],
            'atr14': frame['atr14'],
            'logic': logic
        }
    buy_frames = sum(1 for d in agreement if d == 'BUY')
    sell_frames = sum(1 for d in agreement if d == 'SELL')
    neutral_frames = sum(1 for d in agreement if d == 'NEUTRAL')
    summary = f"\nMULTI-TIMEFRAME 16/16 STRATEGY ANALYSIS FOR {symbol.upper()} ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"
    for label in ['H1', 'H4', 'D1']:
        if label in results:
            frame = results[label]
            summary += f"{label}: {frame['direction']} ({frame['bullish_count']} bullish conf)\n"
            summary += f"    EMA9: {frame.get('ema9','')} | EMA21: {frame.get('ema21','')} | RSI14: {frame.get('rsi14','')}\n"
            summary += f"    Bullish Engulf: {frame.get('bullish_engulf',False)} | Body>50%: {frame.get('body_50',False)}\n"
            if frame.get('adx14') is not None: summary += f"    ADX14: {frame['adx14']:.2f}\n"
            if frame.get('atr14') is not None: summary += f"    ATR14: {frame['atr14']:.5f}\n"
            summary += f"    Checks: {'/'.join(frame['logic']) if frame['logic'] else 'None'}\n\n"
    summary += f"Multi-Frame Agreement: {buy_frames}/3 BUY, {sell_frames}/3 SELL, {neutral_frames}/3 NEUTRAL\n"
    summary += "\nMANUAL CHECKS REQUIRED:\n- [ ] News/Economic Calendar\n- [ ] Spread/Commission OK for entry?\n- [ ] Group/Forum Sentiment or warnings\n"
    summary += "\n---------------------------\n"
    summary += f"Final Confidence: {sum(confirmations.values())}/16 (auto criteria only)\n"
    summary += "If all manual checks pass and multi-frame is BUY (or SELL), trade is allowed.\n"
    return summary

# --- TELEGRAM COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("❌ Access denied.")
        return
    await update.message.reply_text("✅ Cloud bot online. Telegram working!")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("❌ Access denied.")
        return
    await update.message.reply_text("Pong! I am online.")

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("❌ Access denied.")
        return
    try:
        if not context.args:
            await update.message.reply_text("Usage: /analyze SYMBOL (e.g. /analyze EURUSD)")
            return
        symbol = context.args[0].upper()
        msg = multi_frame_analyze(symbol)
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("analyze", analyze))
    app.run_polling()
