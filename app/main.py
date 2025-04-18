import asyncio

from app.handlers.command_handler import command_router
from app.handlers.message_handler import message_router
from settings import settings
from app.logger.logging_tool import logger

from aiogram import Bot, Dispatcher


async def main():
    logger.info("Starting conversation AIBot")
    bot = Bot(token=settings.get_telegram_bot_token())
    dp = Dispatcher()
    dp.include_routers(command_router, message_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


asyncio.run(main())
