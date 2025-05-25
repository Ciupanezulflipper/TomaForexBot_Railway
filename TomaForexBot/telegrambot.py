import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from botstrategies import analyze_symbol_single
from charting import generate_pro_chart
from statushandler import get_bot_status
from marketdata import get_ohlc

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/start called by {update.effective_user.username}, args: {context.args if hasattr(context,'args') else 'None'}")
    await update.message.reply_text("👋 Bot is online. Use /analyze EURUSD or /chart EURUSD H1")

# /status
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/status called by {update.effective_user.username}, args: {context.args if hasattr(context,'args') else 'None'}")
    status = get_bot_status()
    await update.message.reply_text(status)

# /analyze SYMBOL
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/analyze called by {update.effective_user.username}, args: {context.args}")
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /analyze SYMBOL (e.g. /analyze EURUSD)")
        return
    symbol = context.args[0].upper()
    chat_id = update.effective_chat.id
    try:
        from analyzers import analyze_symbol_multi_tf
        logger.debug(f"Using analyze_symbol_multi_tf for {symbol}")
        await analyze_symbol_multi_tf(symbol, chat_id)
    except ImportError:
        logger.debug(f"Using analyze_symbol_single for {symbol}")
        result = await analyze_symbol_single(symbol)
        await update.message.reply_text(result)

# /chart SYMBOL TIMEFRAME
async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/chart called by {update.effective_user.username}, args: {context.args}")
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: /chart SYMBOL TIMEFRAME (e.g. /chart EURUSD H1)")
        return
    symbol = context.args[0].upper()
    tf = context.args[1].upper()
    chat_id = update.effective_chat.id
    logger.debug(f"Fetching data for {symbol} {tf}")

    try:
        df = get_ohlc(symbol, tf, bars=150)
        logger.debug(f"get_ohlc returned: {df.shape if df is not None else 'None'}")
        if df is None or df.empty:
            await update.message.reply_text("❌ No data available for chart.")
            return
        chart_path = generate_pro_chart(df, symbol, tf)
        with open(chart_path, 'rb') as photo:
            await context.bot.send_photo(chat_id=chat_id, photo=photo)
    except Exception as e:
        logger.error(f"Chart error for {symbol}: {e}")
        await update.message.reply_text(f"⚠️ Chart error: {e}")

# /echo
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/echo called by {update.effective_user.username}, args: {context.args if hasattr(context,'args') else 'None'}")
    await update.message.reply_text("Bot is alive!")

# Start Telegram bot listener
def start_telegram_listener():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("chart", chart_command))
    app.add_handler(CommandHandler("echo", echo))

    logger.info("[INFO] Telegram bot started. Listening for commands...")
    app.run_polling()
