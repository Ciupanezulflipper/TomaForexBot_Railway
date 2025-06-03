# auto_menu_bot.py
import os
import logging
import inspect
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, CallbackQueryHandler, ApplicationBuilder
)

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Command Registry (class version) ---
class CommandRegistry:
    def __init__(self):
        self.commands = {}
        self.categories = {
            'main': [],
            'trading': [],
            'portfolio': [],
            'alerts': [],
            'settings': [],
            'analysis': [],
            'news': [],
            'admin': []
        }

    def register(self, name, description, category='main', emoji='🔹'):
        self.commands[name] = {
            'description': description,
            'category': category,
            'emoji': emoji
        }
        if name not in self.categories[category]:
            self.categories[category].append(name)

    def info(self, name):
        return self.commands.get(name, {})

    def in_category(self, category):
        return self.categories.get(category, [])

    def all(self):
        return list(self.commands.keys())

def command_auto_register(description, category='main', emoji='🔹'):
    def decorator(func):
        func._auto_command = {'description': description, 'category': category, 'emoji': emoji}
        return func
    return decorator

class TomaForexBot:
    def __init__(self, token):
        self.registry = CommandRegistry()
        self.token = token
        self.app = Application.builder().token(token).build()
        self._auto_setup()

    def _auto_setup(self):
        # Register all commands from class methods
        for name, method in inspect.getmembers(self, inspect.ismethod):
            info = getattr(method, '_auto_command', None)
            if info:
                self.registry.register(name.replace('_command', ''), **info)
                self.app.add_handler(CommandHandler(name.replace('_command', ''), method))
        # Register menu/help/callback
        self.app.add_handler(CommandHandler("menu", self.menu_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))

    def menu_keyboard(self):
        kb = []
        for cat in ['main', 'trading', 'analysis', 'news', 'alerts', 'settings', 'portfolio']:
            cmds = self.registry.in_category(cat)
            if not cmds:
                continue
            row = []
            for cmd in cmds:
                info = self.registry.info(cmd)
                row.append(InlineKeyboardButton(
                    f"{info['emoji']} /{cmd}",
                    callback_data=f"cmd_{cmd}"
                ))
                if len(row) == 2:
                    kb.append(row)
                    row = []
            if row:
                kb.append(row)
        return InlineKeyboardMarkup(kb)

    @command_auto_register("Start the bot and show welcome message", category='main', emoji='🚀')
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👋 Bot is online. Use /menu to see available commands."
        )

    @command_auto_register("Get economic calendar", category='news', emoji='📅')
    async def calendar_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Your real economic calendar logic here:
        await update.message.reply_text("Economic calendar auto-registered! (Plug in your logic here.)")

    @command_auto_register("Get news for a symbol", category='news', emoji='📰')
    async def news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📰 News logic auto-registered!")

    @command_auto_register("Show technical analysis", category='analysis', emoji='📊')
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📊 Analysis logic auto-registered!")

    @command_auto_register("Show chart", category='analysis', emoji='🗺️')
    async def chart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🗺️ Chart logic auto-registered!")

    @command_auto_register("Manage price alerts", category='alerts', emoji='🔔')
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔔 Alerts auto-registered!")

    @command_auto_register("View portfolio", category='portfolio', emoji='💼')
    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("💼 Portfolio auto-registered!")

    @command_auto_register("Bot settings", category='settings', emoji='⚙️')
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⚙️ Settings auto-registered!")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = "📚 *Available Commands:*\n\n"
        for cat in self.registry.categories:
            cmds = self.registry.in_category(cat)
            if not cmds:
                continue
            msg += f"*{cat.title()}*\n"
            for cmd in cmds:
                info = self.registry.info(cmd)
                msg += f"{info['emoji']} /{cmd} - {info['description']}\n"
            msg += "\n"
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            f"🎛️ Main Menu ({len(self.registry.commands)} commands)",
            reply_markup=self.menu_keyboard()
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data.startswith("cmd_"):
            name = query.data.replace("cmd_", "")
            info = self.registry.info(name)
            await query.edit_message_text(
                f"{info['emoji']} /{name}\n\n{info['description']}",
                parse_mode='Markdown'
            )

    def start(self):
        self.app.run_polling()

if __name__ == "__main__":
    bot = TomaForexBot(TELEGRAM_TOKEN)
    bot.start()
