import os
import sys
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from datetime import datetime

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUR_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# Validate all required keys
def validate_env():
    if not OPENAI_API_KEY or not OPENAI_API_KEY.startswith("sk-"):
        print("❌ OPENAI_API_KEY missing or invalid.")
        sys.exit(1)
    if not TELEGRAM_BOT_TOKEN or ":" not in TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN missing or invalid.")
        sys.exit(1)
    if not YOUR_CHAT_ID or not YOUR_CHAT_ID.lstrip("-").isdigit():
        print("❌ YOUR_CHAT_ID missing or invalid.")
        sys.exit(1)

validate_env()

# Initialize OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

class ChatGPTTelegramBot:
    def __init__(self):
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("ping", self.ping_owner))
        self.application.add_handler(CommandHandler("ask", self.ask_chatgpt))
        self.application.add_handler(CommandHandler("summary", self.send_summary))
        self.application.add_handler(CommandHandler("signal", self.send_signal_example))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Hi! I'm your assistant bot.\n"
            "Commands:\n"
            "/ask <question>\n"
            "/ping <msg>\n"
            "/summary\n"
            "/signal"
        )

    async def ping_owner(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        msg = f"🔔 Ping from {user.full_name} (@{user.username})\n"
        if context.args:
            msg += "Message: " + ' '.join(context.args)
        await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=msg)
        await update.message.reply_text("✅ Admin notified!")

    async def ask_chatgpt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Use: /ask What is inflation?")
            return
        prompt = ' '.join(context.args)
        await self.process_chatgpt(update, prompt)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.process_chatgpt(update, update.message.text)

    async def process_chatgpt(self, update: Update, prompt: str):
        try:
            await update.message.reply_chat_action("typing")
            response = await self.get_openai_response(prompt)
            await update.message.reply_text(response)
            await self.log_usage(update.effective_user, prompt, response)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error: {str(e)}")

    async def get_openai_response(self, prompt: str):
        chat = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return chat.choices[0].message.content.strip()

    async def log_usage(self, user, prompt: str, response: str):
        msg = (
            f"📊 ChatGPT Usage\n"
            f"👤 User: {user.full_name} (@{user.username})\n"
            f"📥 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n"
            f"📤 Response: {len(response)} chars"
        )
        await self.application.bot.send_message(chat_id=YOUR_CHAT_ID, text=msg)

    async def send_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        summary = (
            f"📈 <b>Daily Summary</b>\n"
            f"Date: {now} UTC\n"
            f"Users: 1\n"
            f"Requests: [mocked] 23\n"
            f"Top Topic: EUR/USD"
        )
        await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=summary, parse_mode="HTML")
        await update.message.reply_text("✅ Summary sent.")

    async def send_signal_example(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        signal = (
            "🎯 <b>TRADE SIGNAL</b>\n\n"
            "<b>EUR/USD</b> 🔵 <b>BUY</b>\n"
            "📊 Score: 91% (A+)\n"
            "🎯 Entry: 1.0830\n"
            "🛑 SL: 1.0805\n"
            "🎁 TP: 1.0900\n"
            "📈 R/R: 1:2.8\n\n"
            "✅ RSI divergence\n"
            "✅ Volume spike\n"
            "✅ News confidence: 88%\n"
            "✅ Timing: London session\n\n"
            "⚠️ Not financial advice."
        )
        await update.message.reply_text(signal, parse_mode="HTML")

    def run(self):
        print("🚀 Telegram Bot Running...")
        self.application.run_polling()

if __name__ == "__main__":
    bot = ChatGPTTelegramBot()
    bot.run()
