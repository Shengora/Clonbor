import asyncio
import logging
from aiogram import Bot, Dispatcher

from bot.core.config import BOT_TOKEN
from bot.database.db import init_db
from bot.handlers import register_all_handlers
from bot.core.userbot import userbot_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Initializing database...")
    await init_db()

    logger.info("Starting userbots...")
    await userbot_manager.start_all()

    bot = Bot(token=BOT_TOKEN)

    from bot.core.forwarder import forwarder
    forwarder.set_bot(bot)

    dp = Dispatcher()

    register_all_handlers(dp)

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await userbot_manager.stop_all()

if __name__ == "__main__":
    asyncio.run(main())
