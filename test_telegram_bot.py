
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[DEBUG] /start received")
    await update.message.reply_text("✅ Bot is alive and responding!")

if __name__ == "__main__":
    print("[INFO] Starting minimal bot...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
