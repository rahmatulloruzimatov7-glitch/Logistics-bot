import os
import asyncio
import logging
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
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"👋 Salom! Men logistika hisobotlari botiman.\n\n"
        f"Reys hisobotini yuboring — men uni Google Sheetsga kiritaman.\n\n"
        f"📌 Bu chatning ID si: {chat_id}"
    )


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not set in .env")
        return

    async def _run():
        app = Application.builder().token(token).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_report))
        logger.info("Bot started — waiting for messages...")
        async with app:
            await app.start()
            await app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            await asyncio.Event().wait()
            await app.updater.stop()
            await app.stop()

    asyncio.run(_run())


if __name__ == "__main__":
    main()
