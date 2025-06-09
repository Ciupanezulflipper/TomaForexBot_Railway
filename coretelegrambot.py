import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from secure_env_loader import load_env
from signal_fusion import run_fused_analysis

load_env()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi! I'm your Forex Assistant Bot. Use /signal to get the latest trade signals.")

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
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
