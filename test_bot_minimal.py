from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7684081650:AAHkNK7E8McCcYiZzY84z3xsrkNckwOtY4o"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[DEBUG] /start received")
    await update.message.reply_text("pong")

if __name__ == "__main__":
    print("[INFO] Minimal test bot starting...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("[INFO] Telegram bot polling started. Now send /start to your bot in Telegram.")
    app.run_polling()
