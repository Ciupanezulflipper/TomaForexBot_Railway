import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

from botstrategies import analyze_symbol_single
from analyzers import analyze_symbol_multi_tf
from charting import generate_pro_chart_async
from marketdata import get_ohlc
from news_sentiment import get_news_sentiment
from economic_calendar_module import fetch_major_events
from statushandler import get_bot_status, handle_status

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────── Command Handlers ────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot is online. Use:\n"
        "/analyze EURUSD\n"
        "/chart EURUSD H1\n"
        "/news EURUSD\n"
        "/calendar\n"
        "/status"
    )

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[DEBUG] /analyze command triggered")
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /analyze SYMBOL")
        return

    symbol = context.args[0].upper()
    print(f"[DEBUG] Analyzing symbol: {symbol}")

    try:
        result = await analyze_symbol_multi_tf(symbol, update.effective_chat.id)
        print(f"[DEBUG] Analysis result: {result}")

        if not result.get("confirmed"):
            await update.message.reply_text(f"⚠️ No strong signal for {symbol}.\nReason: {result.get('reason')}")
        else:
            await update.message.reply_text(
                f"✅ Signal for {symbol}: {result.get('signal')} ({result.get('avg_score'):.2f})\n"
                f"{result.get('reason')}"
            )
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        await update.message.reply_text(f"❌ Error analyzing {symbol}: {e}")

async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: /chart SYMBOL TIMEFRAME (e.g., /chart EURUSD H1)")
        return

    symbol = context.args[0].upper()
    tf = context.args[1].upper()

    try:
        df = await get_ohlc(symbol, tf)
        if df is None or df.empty:
            await update.message.reply_text("❌ No data for that symbol/timeframe.")
            return

        chart_path = await generate_pro_chart_async(df, symbol, tf)
        with open(chart_path, 'rb') as img:
            await update.message.reply_photo(photo=img)

    except Exception as e:
        logger.error(f"Chart error: {e}")
        await update.message.reply_text(f"❌ Chart generation failed: {e}")

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /news SYMBOL (e.g., /news USDJPY)")
        return

    symbol = context.args[0].upper()
    try:
        sentiment = get_news_sentiment(symbol)
        await update.message.reply_text(f"📲 {symbol} News Sentiment: {sentiment}")
    except Exception as e:
        logger.error(f"News error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        events = fetch_major_events()
        if not events:
            await update.message.reply_text("📅 No major economic events right now.")
            return

        msg = ""
        for e in events[:6]:
            msg += f"{e['date']} - {e['event']} - {e['impact']}\n"

        await update.message.reply_text(msg)

    except Exception as e:
        logger.error(f"Calendar error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

# ──────────────── Bot Launcher ────────────────

def start_telegram_listener():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("chart", chart_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("calendar", calendar_command))

    logging.info("[INFO] Telegram bot initialized.")
    app.run_polling()

if __name__ == "__main__":
    start_telegram_listener()
