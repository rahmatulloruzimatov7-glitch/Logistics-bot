"""Main entry point — Logistics Report Bot.

This bot receives logistics trip reports via Telegram, extracts structured
data using Claude AI, validates against Malumotnoma reference sheet, and
writes confirmed trips to the Reyslar sheet.

Usage:
    python bot.py

Required environment variables (see .env.example):
    TELEGRAM_BOT_TOKEN    — from @BotFather
    ANTHROPIC_API_KEY     — from console.anthropic.com
    GOOGLE_SHEET_ID       — Google Sheets ID
    ERROR_GROUP_CHAT_ID   — Telegram group ID for validation errors
"""
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from handlers.report import handle_report

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def start(update: Update, context) -> None:
    """Handle /start command — show bot info and chat ID."""
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"👋 Salom! Men logistika hisobotlari botiman.\n\n"
        f"Reys hisobotini yuboring — men uni Google Sheetsga kiritaman.\n\n"
        f"📌 Bu chatning ID si: {chat_id}\n"
        f"(Xato guruhini sozlash uchun ERROR_GROUP_CHAT_ID ga shu raqamni kiriting)"
    )


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not set in .env")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_report))
    logger.info("Bot started — waiting for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
