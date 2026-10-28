from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.database.repository import Repository
from bot.database.session import Database
from bot.services.instagram_api import InstagramAPI

db = Database(settings.db_file)
repo = Repository(db)
dp = Dispatcher(storage=MemoryStorage())
ig = InstagramAPI()


def make_bot() -> Bot:
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN .env faylida ko'rsatilmagan.")
    return Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
