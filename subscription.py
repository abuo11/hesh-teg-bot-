import logging
import time

from ..config import cfg
from .. import db

log = logging.getLogger(__name__)
_cache: dict[int, float] = {}


async def check(bot, user_id: int):
    """(obuna_bormi, xatolik_bormi)"""
    if _cache.get(user_id, 0) > time.time():
        return True, False
    try:
        m = await bot.get_chat_member(cfg.channel, user_id)
    except Exception as e:
        log.error("Obuna tekshiruvi xatosi: %s", type(e).__name__)
        await db.log_api("subscription", f"{type(e).__name__}: {e}")
        return False, True
    ok = m.status in ("member", "administrator", "creator")
    if ok:
        _cache[user_id] = time.time() + 60
    return ok, False
