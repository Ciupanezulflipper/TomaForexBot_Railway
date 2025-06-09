import sys
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Add current directory and /core to sys.path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from secure_env_loader import load_env
from signal_fusion import run_fused_analysis
from autoscheduler import start_auto_alerts

# Load environment variables
load_env()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Telegram command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi! I'm your Forex Assistant Bot.\nUse /signal to get fused trade signals.\nAuto-alerts are active.")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Analyzing strategy + news... Please wait...")
    try:
        fused = await run_fused_analysis()
        if not fused:
            await update.message.reply_text("⚠️ No active trades found.")
            return

        msg = "📈 *FUSED SIGNALS*\n\n"
        for entry in fused:
            msg += (
                f"*{entry['pair']}* `{entry['type']}`\n"
                f"Entry: `{entry['entry_price']}` | Live: `{entry['current_price']}`\n"
                f"🧠 Strategy Score: *{entry['strategy_score']}* → Final: *{entry['final_score']}*\n"
                f"🗞️ News: {entry['news_comment']}\n\n"
            )
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error running signal: {str(e)}")

def main():
    # Initialize Telegram bot
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))

    # Start auto-alert scheduler
    start_auto_alerts()

    print("✅ Telegram Bot + Auto-Alert Scheduler running...")
    app.run_polling()

if __name__ == "__main__":
    main()
