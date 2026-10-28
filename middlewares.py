from __future__ import annotations

from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config import settings
from bot.keyboards.inline import subscription_kb
from bot.loader import repo
from bot.services.subscription_service import SubscriptionError, is_subscribed
from bot.utils.ratelimit import RateLimiter

SUB_TEXT = "🔒 Botdan foydalanish uchun avval rasmiy kanalimizga obuna bo‘ling."
_limiter = RateLimiter(settings.rate_limit)


class GuardMiddleware(BaseMiddleware):
    """Foydalanuvchini yozadi, rate-limit va majburiy obunani tekshiradi."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)
        await repo.upsert_user(user.id, user.username, user.first_name)

        if not _limiter.allow(user.id):
            if isinstance(event, CallbackQuery):
                await event.answer("Juda ko‘p so‘rov. Biroz kuting.", show_alert=True)
            return None

        is_check = isinstance(event, CallbackQuery) and (event.data or "") == "sub:check"
        if is_check:
            return await handler(event, data)
        try:
            ok = await is_subscribed(self.bot, user.id)
        except SubscriptionError:
            await self._reply(event, "⚠️ Obunani tekshirib bo‘lmadi. Bot kanalda admin ekanini tekshiring "
                                     "yoki birozdan so‘ng qayta urinib ko‘ring.")
            return None
        if not ok:
            await self._reply(event, SUB_TEXT, subscription_kb())
            return None
        await repo.bump("action")
        return await handler(event, data)

    @staticmethod
    async def _reply(event, text: str, kb=None):
        if isinstance(event, CallbackQuery):
            await event.answer()
            if event.message:
                await event.message.answer(text, reply_markup=kb)
        elif isinstance(event, Message):
            await event.answer(text, reply_markup=kb)
