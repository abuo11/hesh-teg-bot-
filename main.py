from __future__ import annotations

import asyncio

from aiogram.types import BotCommand
from aiohttp import web

from bot.config import settings
from bot.handlers import admin, bio, generator, hashtag, history, start, subscription, video_analysis
from bot.loader import dp, make_bot
from bot.middlewares import GuardMiddleware
from bot.utils.logger import logger
from bot.webapi import create_app


async def main() -> None:
    bot = make_bot()
    guard = GuardMiddleware(bot)
    dp.message.outer_middleware(guard)
    dp.callback_query.outer_middleware(guard)
    # subscription router birinchi: "sub:check" middleware'dan o'tib ketadi
    for r in (subscription.router, start.router, hashtag.router, generator.router,
              video_analysis.router, bio.router, history.router, admin.router):
        dp.include_router(r)

    await bot.set_my_commands([
        BotCommand(command="start", description="Botni boshlash"),
        BotCommand(command="history", description="Oxirgi natijalar"),
        BotCommand(command="help", description="Yordam"),
    ])

    runner = web.AppRunner(create_app(bot))
    await runner.setup()
    await web.TCPSite(runner, settings.web_host, settings.web_port).start()
    logger.info("Web App serveri: http://%s:%s", settings.web_host, settings.web_port)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot ishga tushdi")
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
