from telegram import Update
from telegram.ext import CallbackContext
from botstrategies import (
    analyze_gold,
    analyze_silver,
    analyze_eurusd,
    analyze_all,
    analyze_silver_alert,
)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Welcome to Toma's ForexBot!\n\n"
        "📌 Commands available:\n"
        "/gold — Analyze XAUUSD\n"
        "/silver — Analyze XAGUSD\n"
        "/eurusd — Analyze EUR/USD\n"
        "/all — Analyze all three\n\n"
        "🕒 You can also add timeframe and patterns:\n"
        "Examples: /gold 4H 3 | /silver 1D | /all 15M 4\n"
        "Default timeframe: 1H | Default patterns: 2"
    )

def gold(update: Update, context: CallbackContext):
    args = context.args
    timeframe = args[0] if len(args) >= 1 else "1H"
    threshold = int(args[1]) if len(args) >= 2 else 2
    result = analyze_gold(timeframe=timeframe, pattern_threshold=threshold)
    update.message.reply_text(result)

def silver(update: Update, context: CallbackContext):
    args = context.args
    timeframe = args[0] if len(args) >= 1 else "1H"
    threshold = int(args[1]) if len(args) >= 2 else 2
    result = analyze_silver(timeframe=timeframe, pattern_threshold=threshold)
    update.message.reply_text(result)

def eurusd(update: Update, context: CallbackContext):
    args = context.args
    timeframe = args[0] if len(args) >= 1 else "1H"
    threshold = int(args[1]) if len(args) >= 2 else 2
    result = analyze_eurusd(timeframe=timeframe, pattern_threshold=threshold)
    update.message.reply_text(result)

def all(update: Update, context: CallbackContext):
    args = context.args
    timeframe = args[0] if len(args) >= 1 else "1H"
    threshold = int(args[1]) if len(args) >= 2 else 2
    result = analyze_all(timeframe=timeframe, pattern_threshold=threshold)
    update.message.reply_text(result)
from telegram import Update
from telegram.ext import ContextTypes
from botstrategies import analyze_gold, analyze_silver, analyze_eurusd, analyze_all

# ✅ Optional: list valid timeframes you allow
VALID_TIMEFRAMES = ["1M", "5M", "15M", "30M", "1H", "4H", "1D"]

# 📌 /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Toma's ForexBot!\n\n"
        "📌 Commands available:\n"
        "/gold — Analyze XAUUSD\n"
        "/silver — Analyze XAGUSD\n"
        "/eurusd — Analyze EUR/USD\n"
        "/all — Analyze all three\n\n"
        "🕒 You can also add timeframe and patterns:\n"
        "Examples: /gold 4H 3 | /silver 1D | /all 15M 4\n"
        "Default timeframe: 1H | Default patterns: 2"
    )

# 🔍 Core extractor for timeframe + pattern threshold
def extract_args(args):
    tf = "1H"
    pt = 2
    if args:
        if args[0].upper() in VALID_TIMEFRAMES:
            tf = args[0].upper()
        if len(args) > 1 and args[1].isdigit():
            pt = int(args[1])
    return tf, pt

# 💡 Gold handler
async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tf, pt = extract_args(context.args)
    result = analyze_gold(tf, pt)
    await update.message.reply_text(result)

# 💡 Silver handler
async def silver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tf, pt = extract_args(context.args)
    result = analyze_silver(tf, pt)
    await update.message.reply_text(result)

# 💡 EURUSD handler
async def eurusd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tf, pt = extract_args(context.args)
    result = analyze_eurusd(tf, pt)
    await update.message.reply_text(result)

# 💡 All handler
async def all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tf, pt = extract_args(context.args)
    result = analyze_all(tf, pt)
    await update.message.reply_text(result)
