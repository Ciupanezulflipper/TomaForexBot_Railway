from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "PASTE_YOUR_TOKEN_HERE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Ping received")
    await update.message.reply_text("pong")

if __name__ == "__main__":
    print("RUNNING")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
