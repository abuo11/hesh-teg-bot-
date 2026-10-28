from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from bot.config import settings


def cabinet_kb() -> InlineKeyboardMarkup | None:
    if not settings.webapp_url.startswith("https://"):
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📱 Kabinetni ochish", web_app=WebAppInfo(url=settings.webapp_url))
    ]])
