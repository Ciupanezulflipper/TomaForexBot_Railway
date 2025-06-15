import os
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

from botstrategies import analyze_symbol_single
from cloudbot import calendar_command  # reuses your async function

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! TomaBot is alive and running.")

# /analyze command (simple version)
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = "EURUSD"
    timeframe = "H1"
    result = await analyze_symbol_single(symbol, timeframe)
    await update.message.reply_text(f"📊 {symbol} ({timeframe}) Analysis:\n\n{result}")

# Build and run the polling bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("calendar", calendar_command))
    app.add_handler(CommandHandler("analyze", analyze_command))

    print("📡 Bot is polling... Waiting for commands.")
    app.run_polling()
