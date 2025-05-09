# statushandler.py

from telegram import Update
from telegram.ext import ContextTypes
from marketdata import connect
import MetaTrader5 as mt5

async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not mt5.initialize():
        await update.message.reply_text("❌ MT5 not connected.")
        return

    account_info = mt5.account_info()
    if account_info:
        status = (
            f"🟢 MT5 Connected\n"
            f"Account ID: {account_info.login}\n"
            f"Leverage: {account_info.leverage}\n"
            f"Balance: {account_info.balance:.2f}\n"
            f"Equity: {account_info.equity:.2f}\n"
            f"Margin: {account_info.margin:.2f}"
        )
    else:
        status = "⚠️ Could not retrieve MT5 account info."

    await update.message.reply_text(status)
