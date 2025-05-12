import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from botstrategies import analyze_symbol_single, analyze_all_symbols, analyze_many_symbols

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🚨 /start received from {update.effective_user.id}")
    await update.message.reply_text("👋 Hello from Railway. Bot is live.")

async def handle_gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 /gold received from {update.effective_user.id}")
    msg = await analyze_symbol_single("XAUUSD")
    await update.message.reply_text(msg)

async def handle_silver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 /silver received from {update.effective_user.id}")
    msg = await analyze_symbol_single("XAGUSD")
    await update.message.reply_text(msg)

async def handle_us30(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 /us30 received from {update.effective_user.id}")
    msg = await analyze_symbol_single("US30")
    await update.message.reply_text(msg)

async def handle_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 /analyze received from {update.effective_user.id}")
    await update.message.reply_text("⏳ Scanning standard symbol set (H1)...")
    messages = await analyze_all_symbols()
    for msg in messages:
        await update.message.reply_text(msg)

async def handle_scanall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 /scanall received from {update.effective_user.id}")
    await update.message.reply_text("📡 Scanning top 20+ pairs and assets (H1)...")
    messages = await analyze_many_symbols()
    for msg in messages:
        await update.message.reply_text(msg)

async def start_telegram_listener():
    print("🚀 Telegram bot starting...")
    telegram_app.add_handler(CommandHandler("start", handle_start))
    telegram_app.add_handler(CommandHandler("gold", handle_gold))
    telegram_app.add_handler(CommandHandler("silver", handle_silver))
    telegram_app.add_handler(CommandHandler("us30", handle_us30))
    telegram_app.add_handler(CommandHandler("analyze", handle_analyze))
    telegram_app.add_handler(CommandHandler("scanall", handle_scanall))
    print("✅ Handlers ready.")
    await telegram_app.run_polling(stop_signals=None)
