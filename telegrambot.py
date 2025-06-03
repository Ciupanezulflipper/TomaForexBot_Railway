import os
import logging
import time
from datetime import datetime

from dotenv import load_dotenv
import pandas as pd

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

# === IMPORT YOUR MODULES (adjust as needed) ===
from news_sentiment import news_command, get_news_sentiment
from patterns import detect_patterns
from analyzers import analyze_symbol_multi_tf
from alerts import should_alert, build_alert_message
from riskmetrics import calc_atr
from sessions import get_market_session
from botstrategies import analyze_symbol_single
from bothandlers import gold, silver, eurusd, all_handler
from charting import generate_pro_chart_async
from statushandler import get_bot_status
from marketdata import get_ohlc
from economic_calendar_module import fetch_major_events
from macrofilter import check_macro_filter  # If in different file, update this import!

# === CONFIG ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
ALERT_USER = "@TomaForexBot"

# Symbols and timeframes to scan (edit as you wish)
SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY', 'US30', 'XAUUSD']
TIMEFRAMES = ['M5', 'M15']

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# === HEALTH MONITOR ===
health_monitor = None  # Set after app creation

class BotHealthMonitor:
    def __init__(self, bot, admin_chat_id):
        self.bot = bot
        self.admin_chat_id = admin_chat_id
        self.last_heartbeat = time.time()
        self.signals_today = 0
        self.error_count = 0

    async def send_heartbeat(self):
        now = time.time()
        if now - self.last_heartbeat > 3600:
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=f"🟢 Bot alive - Processed {self.signals_today} signals today"
            )
            self.last_heartbeat = now

    async def report_error(self, error):
        self.error_count += 1
        await self.bot.send_message(
            chat_id=self.admin_chat_id,
            text=f"🔴 Bot error detected: {error}"
        )

# === COMMAND HANDLERS ===

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/start called by {update.effective_user.username}, args: {getattr(context,'args', None)}")
    await update.message.reply_text("👋 Bot is online. Use /analyze EURUSD or /chart EURUSD H1")
    if health_monitor:
        await health_monitor.send_heartbeat()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 Available Commands:\n\n"
        "Main\n"
        "🚀 /start - Start the bot and show welcome message\n"
        "❓ /help - Show help and available commands\n"
        "📋 /menu - Show interactive command menu\n\n"
        "Portfolio\n"
        "💼 /portfolio - View your portfolio\n\n"
        "Alerts\n"
        "🔔 /alerts - Manage price alerts\n\n"
        "Settings\n"
        "⚙️ /settings - Bot settings\n\n"
        "Analysis\n"
        "📊 /analyze - Get technical analysis\n"
        "🗺️ /chart - Get chart for symbol/timeframe\n\n"
        "News\n"
        "📰 /news - Get news for a symbol\n"
        "📅 /calendar - Economic calendar\n"
    )
    await update.message.reply_text(help_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/status called by {update.effective_user.username}, args: {getattr(context,'args', None)}")
    status = get_bot_status()
    await update.message.reply_text(status)

async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📆 Fetching economic calendar...")
    try:
        events = fetch_major_events(hours_back=6, hours_forward=12)
        if not events:
            await update.message.reply_text("No high-impact macro news/events in the past 6h or next 12h.")
            return
        msg = ""
        for e in events[:8]:
            msg += (
                f"{e['date']} | {e['event']} | Impact: {e['impact']}\n"
                f"Affected: {e['affected']} | Source: {e['source']}\n\n"
            )
        await update.message.reply_text(msg[:4000])  # Telegram limit
    except Exception as exc:
        await update.message.reply_text(f"❌ Error: {exc}")

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/analyze called by {update.effective_user.username}, args: {context.args}")
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /analyze SYMBOL (e.g. /analyze EURUSD)")
        return
    symbol = context.args[0].upper()
    chat_id = update.effective_chat.id
    try:
        await analyze_symbol_multi_tf(symbol, chat_id)
        if health_monitor:
            await health_monitor.send_heartbeat()
    except Exception as e:
        logger.error(f"Error in analyze_command: {e}")
        if health_monitor:
            await health_monitor.report_error(str(e))

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
        df = await get_ohlc(symbol, tf, bars=150)
        if df is None or df.empty:
            await update.message.reply_text("❌ No data available for chart.")
            return
        chart_path = await generate_pro_chart_async(df, symbol, tf)
        with open(chart_path, 'rb') as photo:
            await context.bot.send_photo(chat_id=chat_id, photo=photo)
        if health_monitor:
            await health_monitor.send_heartbeat()
    except Exception as e:
        logger.error(f"Chart error for {symbol}: {e}")
        await update.message.reply_text(f"⚠️ Chart error: {e}")
        if health_monitor:
            await health_monitor.report_error(str(e))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/echo called by {update.effective_user.username}, args: {getattr(context,'args', None)}")
    await update.message.reply_text("Bot is alive!")
    if health_monitor:
        await health_monitor.send_heartbeat()

# === SCHEDULED TRADE ALERT HANDLER ===

async def scheduled_signal_scan(context: ContextTypes.DEFAULT_TYPE):
    logger.debug("[SignalScan] Running scheduled_signal_scan...")
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            try:
                # Macro/news filter: skip if high-impact event
                macro_ok = check_macro_filter(symbol, window_minutes=30)
                if macro_ok.get('block'):
                    logger.info(f"[SignalScan] Macro block for {symbol}: {macro_ok['note']}")
                    continue

                # Technicals: your 16+6 strategy, must return dict with .confirmed, .signal
                df = await get_ohlc(symbol, tf, bars=100)
                if df is None or df.empty:
                    continue

                tech = await analyze_symbol_multi_tf(symbol, TELEGRAM_CHAT_ID, test_only=True)
                if not tech.get('confirmed'):
                    continue

                # News sentiment: only trade if aligns with technical
                sentiment = get_news_sentiment(symbol)
                if sentiment not in ['BULLISH', 'BEARISH']:
                    continue

                # Direction match: Only send alert if both agree
                if ((tech['signal'] == 'BUY' and sentiment == 'BULLISH') or
                    (tech['signal'] == 'SELL' and sentiment == 'BEARISH')):

                    entry = df['close'].iloc[-1]
                    atr = calc_atr(df)
                    if tech['signal'] == 'BUY':
                        sl = entry - atr
                        tp = entry + 2*atr
                    else:
                        sl = entry + atr
                        tp = entry - 2*atr

                    chart_path = await generate_pro_chart_async(df, symbol, tf)
                    caption = (
                        f"{ALERT_USER}\n"
                        f"#{symbol} ({tf})\n"
                        f"✅ Signal: <b>{tech['signal']}</b>\n"
                        f"Entry: {entry:.5f}\n"
                        f"SL: {sl:.5f} ({int(atr*10000)}p ATR)\n"
                        f"TP: {tp:.5f} (R:R 1:2)\n"
                        f"Reason: News ({sentiment}) + Technical ({tech.get('reason','')})\n"
                        f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
                    )
                    with open(chart_path, 'rb') as img:
                        await context.bot.send_photo(
                            chat_id=TELEGRAM_CHAT_ID,
                            photo=img,
                            caption=caption,
                            parse_mode='HTML'
                        )
                    logger.info(f"[SignalScan] Alert sent for {symbol} {tf}")

            except Exception as e:
                logger.error(f"[SignalScan] Error for {symbol} {tf}: {e}")

# === BOT LAUNCH ===

def start_telegram_listener():
    global health_monitor
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    health_monitor = BotHealthMonitor(app.bot, TELEGRAM_CHAT_ID)

    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("chart", chart_command))
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("gold", gold))
    app.add_handler(CommandHandler("silver", silver))
    app.add_handler(CommandHandler("eurusd", eurusd))
    app.add_handler(CommandHandler("all", all_handler))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("calendar", calendar_command))

    # Scheduled jobs
    app.job_queue.run_repeating(scheduled_signal_scan, interval=900, first=60)  # Every 15min

    logger.info("[INFO] Telegram bot started. Listening for commands and scanning for trades...")
    app.run_polling()

if __name__ == "__main__":
    start_telegram_listener()
