import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database.engine import init_db
from handlers.admin import actual_notsend, images, messaging, raffle_admin, stats
from handlers.moderation import mod_queue
from handlers.user import actual, content, notifications, raffle, share, start, suggest
from middlewares.access import AccessControlMiddleware, PrivateOnlyMiddleware
from utils.scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.message.middleware(PrivateOnlyMiddleware())
    dp.callback_query.middleware(PrivateOnlyMiddleware())
    dp.message.middleware(AccessControlMiddleware())
    dp.callback_query.middleware(AccessControlMiddleware())

    # Admin routers first so admin commands aren't shadowed by user flows.
    dp.include_router(messaging.router)
    dp.include_router(stats.router)
    dp.include_router(raffle_admin.router)
    dp.include_router(actual_notsend.router)
    dp.include_router(images.router)
    dp.include_router(mod_queue.router)

    dp.include_router(start.router)
    dp.include_router(content.router)
    dp.include_router(share.router)
    dp.include_router(suggest.router)
    dp.include_router(raffle.router)
    dp.include_router(actual.router)
    dp.include_router(notifications.router)

    await init_db()
    setup_scheduler(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
