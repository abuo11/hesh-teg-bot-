from __future__ import annotations

import time

from aiogram import Bot
from aiogram.enums import ChatMemberStatus

from bot.config import settings
from bot.utils.logger import logger

OK = {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}
_cache: dict[int, float] = {}
TTL = 120


class SubscriptionError(Exception):
    pass


async def is_subscribed(bot: Bot, user_id: int, use_cache: bool = True) -> bool:
    if user_id in settings.admin_ids:
        return True
    if use_cache and _cache.get(user_id, 0) > time.time():
        return True
    try:
        m = await bot.get_chat_member(settings.required_channel, user_id)
    except Exception as e:
        logger.error("Obuna tekshiruvi xatosi: %s", e)
        raise SubscriptionError(str(e)) from e
    ok = m.status in OK
    if ok:
        _cache[user_id] = time.time() + TTL
    else:
        _cache.pop(user_id, None)
    return ok


def clear_cache() -> None:
    _cache.clear()
