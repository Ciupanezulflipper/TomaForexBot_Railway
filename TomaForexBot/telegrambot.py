# TomaForexBot/telegrambot.py

import os
from dotenv import load_dotenv
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from telegramsender import send_telegram_message, send_telegram_photo
from logger import CSV_FILE
from marketdata import get_mt5_data
from analyzers import analyze_symbol_multi_tf

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# Build the Telegram bot application
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# ✅ /start
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🚨 Received /start from {update.effective_user.id}")
    await update.message.reply_text("👋 Bot is active and ready. Use /help to see available commands.")

# ✅ /help
def send_help_menu():
    return (
        "🤖 TomaForexBot – Command Menu\n\n"
        "📊 /analyze – Run all symbols (H1)\n"
        "📊 /analyze EURUSD M15 – Single symbol + timeframe\n"
        "🧠 /analyze EURUSD multi – H1 + H4 + D1 summary\n"
        "📈 /chart SYMBOL – Chart with explanation\n"
        "📁 /csv – Send trade_signals.csv\n"
        "🔧 /help – Show this menu"
    )

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 Received /help from {update.effective_user.id}")
    await update.message.reply_text(send_help_menu())

# ✅ /csv
async def handle_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 Received /csv from {update.effective_user.id}")
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "rb") as f:
            await update.message.reply_document(document=InputFile(f), filename="trade_signals.csv")
    else:
        await update.message.reply_text("❌ No CSV file found.")

# ✅ /chart SYMBOL
async def handle_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 Received /chart from {update.effective_user.id}")
    if not context.args:
        await update.message.reply_text("❌ Usage: /chart SYMBOL")
        return

    symbol = context.args[0].upper()
    df = get_mt5_data(symbol, timeframe="H1", bars=200)
    if df is None or df.empty:
        await update.message.reply_text(f"❌ No data returned for {symbol}")
        return

    results = await analyze_symbol_multi_tf(df, symbol)
    if results:
        result = results[0]
        message = (
            f"{result['timestamp']} – {result['symbol']} ({result['timeframe']})\n"
            f"Signal: {result['signal']} | Score: {result['score']}\n"
            f"Pattern: {result['pattern']}\n"
            f"RSI: {result['rsi']:.2f} | EMA9: {result['ema9']:.4f} | EMA21: {result['ema21']:.4f}\n"
            f"Reasons: {result['reasons']}"
        )
        await update.message.reply_text(message)

        chart_path = f"charts/{symbol}_H1_pro_chart.png"
        if os.path.exists(chart_path):
            await send_telegram_photo(chart_path)
    else:
        await update.message.reply_text("❌ No signal found.")

# ✅ Start polling with debug info
async def start_telegram_listener():
    print("🚀 Telegram listener starting...")
    telegram_app.add_handler(CommandHandler("start", handle_start))
    telegram_app.add_handler(CommandHandler("help", handle_help))
    telegram_app.add_handler(CommandHandler("csv", handle_csv))
    telegram_app.add_handler(CommandHandler("chart", handle_chart))
    print("✅ Handlers added. Bot is polling...")
    await telegram_app.run_polling(stop_signals=None)
