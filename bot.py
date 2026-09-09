def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not set in .env")
        return

    import asyncio
    
    async def _run():
        app = Application.builder().token(token).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_report))
        logger.info("Bot started — waiting for messages...")
        async with app:
            await app.start()
            await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            await asyncio.Event().wait()
            await app.updater.stop()
            await app.stop()

    asyncio.run(_run())


if __name__ == "__main__":
    main()
