import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update, Bot
import pandas as pd

# Import your existing modules
from botstrategies import analyze_symbol_single
from core.signal_fusion import generate_trade_decision
from charting import generate_pro_chart_async
from marketdata import get_ohlc, get_mt5_data
from economic_calendar_module import fetch_major_events, fetch_all_calendar, analyze_events
from statushandler import handle_status
from news_fetcher import fetch_combined_news
from news_signal_logic import analyze_multiple_headlines
from news_feeds import analyze_all_feeds
from patterns import detect_candle_patterns
from indicators import calculate_rsi

# Environment setup
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global bot instance for alerts
bot = Bot(token=TELEGRAM_TOKEN)

def score_bar(score):
    units = min(abs(score), 5)
    blocks = "█" * units
    return f"{blocks}{'🔺' if score > 0 else '🔻'}" if score != 0 else "—"

# ══════════════════ COMMAND HANDLERS ══════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 TomaForexBot is online! Use:\n"
        "/analyze EURUSD - Technical analysis\n"
        "/chart EURUSD H1 - Generate chart\n"
        "/news EURUSD - News sentiment\n"
        "/calendar - Economic events\n"
        "/status - Bot status"
    )

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /analyze SYMBOL")
        return

    symbol = context.args[0].upper()
    try:
        result = await generate_trade_decision(symbol, update.effective_chat.id)
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
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        await update.message.reply_text("⚠️ Usage: /news SYMBOL (e.g., /news USDJPY)")
        return

    try:
        headlines = await fetch_combined_news()
        result = analyze_multiple_headlines(headlines, symbol)
        if result["score"] == 0:
            await update.message.reply_text(f"📰 No strong news signal for {symbol}")
        else:
            msg = (
                f"📊 News Signal for {symbol}\n"
                f"Score: {result['score']} {score_bar(result['score'])}\n"
                f"Reasons:\n" + "\n".join(result['reasons'])
            )
            await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"News command error: {e}")
        await update.message.reply_text(f"❌ Error fetching news: {e}")

async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        events = fetch_major_events()
        if not events:
            await update.message.reply_text("📅 No major economic events right now.")
            return

        msg = "📅 Upcoming Economic Events:\n\n"
        for e in events[:6]:
            msg += f"{e['date']} - {e['event']} - {e['impact']}\n"

        await update.message.reply_text(msg)

    except Exception as e:
        logger.error(f"Calendar error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

# ══════════════════ BACKGROUND ALERT SYSTEM ══════════════════

async def send_pattern_alerts():
    """Send pattern-based trading alerts"""
    PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
    TIMEFRAME = "H1"
    MIN_RSI_BUY = 35
    MAX_RSI_SELL = 65
    
    for symbol in PAIRS:
        try:
            df = get_mt5_data(symbol, TIMEFRAME, bars=100)
            if df is None or df.empty:
                logger.warning(f"[{symbol}] No data.")
                continue

            df = detect_candle_patterns(df)
            rsi = calculate_rsi(df["close"], 14)
            df["RSI"] = rsi

            last = df.iloc[-1]
            last_pattern = last.get("Pattern", "")
            last_rsi = last.get("RSI", None)
            last_close = last.get("close", None)

            alert = None

            # Bullish patterns + low RSI = Buy alert
            if any(p in last_pattern for p in ["Bullish Engulfing", "Hammer", "Morning Star"]):
                if last_rsi is not None and last_rsi < MIN_RSI_BUY:
                    alert = f"🚀 BUY Signal on {symbol} ({TIMEFRAME})\nPattern: {last_pattern}\nRSI: {last_rsi:.2f}\nClose: {last_close}"

            # Bearish patterns + high RSI = Sell alert
            if any(p in last_pattern for p in ["Bearish Engulfing", "Shooting Star", "Evening Star"]):
                if last_rsi is not None and last_rsi > MAX_RSI_SELL:
                    alert = f"📉 SELL Signal on {symbol} ({TIMEFRAME})\nPattern: {last_pattern}\nRSI: {last_rsi:.2f}\nClose: {last_close}"

            if alert:
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=alert)
                logger.info(f"[ALERT SENT] {symbol} - {last_pattern}")

        except Exception as e:
            logger.error(f"[PATTERN ALERT ERROR] {symbol}: {e}")

async def send_news_and_events():
    """Send news and economic calendar alerts"""
    try:
        # News signals
        logic_alerts, events = analyze_all_feeds()
        for alert in logic_alerts[:5]:  # Limit to top 5
            msg = f"📰 {alert['headline'][:100]}...\n=> {alert['asset']} {alert['signal']}\nReason: {alert['reason']}"
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

        # Economic calendar
        major_events = analyze_events(fetch_all_calendar())
        for event in major_events[:3]:  # Only most urgent events
            msg = f"🗓 {event['date']} | {event['event']}\nImpact: {event['impact']} | Affected: {event['affected']}"
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

    except Exception as e:
        logger.error(f"[NEWS/EVENTS ERROR] {e}")

async def background_alerts():
    """Background task for sending periodic alerts"""
    logger.info("Background alert system started")
    while True:
        try:
            await send_pattern_alerts()
            await send_news_and_events()
            logger.info("Alert cycle completed")
        except Exception as e:
            logger.error(f"[BACKGROUND ALERTS ERROR] {e}")
        
        # Wait 15 minutes before next alert cycle
        await asyncio.sleep(60 * 15)

# ══════════════════ MAIN BOT RUNNER ══════════════════

async def run_bot():
    """Main function that runs both command handling and background alerts"""
    # Create the application
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("chart", chart_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("calendar", calendar_command))

    logger.info("🤖 TomaForexBot initialized with command handlers")

    # Start background task for alerts
    alert_task = asyncio.create_task(background_alerts())
    
    # Start polling (this will run indefinitely)
    async with app:
        await app.start()
        logger.info("🔄 Bot polling started")
        
        # Run both polling and background alerts concurrently
        await asyncio.gather(
            app.updater.start_polling(),
            alert_task
        )

if __name__ == "__main__":
    logger.info("🚀 Starting TomaForexBot (Railway deployment)")
    
    # Check environment variables
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN not found in environment")
        exit(1)
    
    if not TELEGRAM_CHAT_ID:
        logger.warning("⚠️ TELEGRAM_CHAT_ID not set")
    
    # Run the bot
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        exit(1)