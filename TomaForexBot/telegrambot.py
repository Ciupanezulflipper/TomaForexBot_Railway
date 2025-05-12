import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from botstrategies import analyze_symbol_single, analyze_all_symbols

# Load .env vars
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# Init bot
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# /start
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🚨 /start received from {update.effective_user.id}")
    await update.message.reply_text("👋 Hello from Railway. Bot is live.")

# /gold
async def handle_gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 /gold received from {update.effective_user.id}")
    msg = await analyze_symbol_single("XAUUSD")
    await update.message.reply_text(msg)

# /us30
async def handle_us30(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 /us30 received from {update.effective_user.id}")
    msg = await analyze_symbol_single("US30")
    await update.message.reply_text(msg)

# /analyze
async def handle_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 /analyze received from {update.effective_user.id}")
    await update.message.reply_text("⏳ Scanning all symbols (H1)...")
    messages = await analyze_all_symbols()
    for msg in messages:
        await update.message.reply_text(msg)

# Start bot
async def start_telegram_listener():
    print("🚀 Telegram bot starting...")
    telegram_app.add_handler(CommandHandler("start", handle_start))
    telegram_app.add_handler(CommandHandler("gold", handle_gold))
    telegram_app.add_handler(CommandHandler("us30", handle_us30))
    telegram_app.add_handler(CommandHandler("analyze", handle_analyze))
    print("✅ Handlers ready.")
    await telegram_app.run_polling(stop_signals=None)
