"""Kabinet (Web App) uchun HTTP API + statik fayllar. Faqat 3 ta funksiya: hashtag, bio, history."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from aiohttp import web

from bot.config import settings
from bot.loader import ig, repo
from bot.services.bio_service import get_bio
from bot.services.caption_analyzer import get_reel_caption
from bot.services.instagram_api import SourceError
from bot.services.subscription_service import SubscriptionError, is_subscribed
from bot.utils.logger import logger
from bot.utils.ratelimit import RateLimiter

_limiter = RateLimiter(max(settings.rate_limit, 10))


def validate_init_data(init_data: str, token: str, max_age: int = 86400) -> dict | None:
    """Telegram Web App initData imzosini tekshiradi. To'g'ri bo'lsa user dict qaytaradi."""
    if not init_data or not token:
        return None
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received = pairs.pop("hash", None)
    if not received:
        return None
    check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, received):
        return None
    try:
        if time.time() - int(pairs.get("auth_date", "0")) > max_age:
            return None
        return json.loads(pairs["user"])
    except (KeyError, ValueError):
        return None


def _err(msg: str, status: int = 400) -> web.Response:
    return web.json_response({"ok": False, "error": msg}, status=status)


def _ok(data) -> web.Response:
    return web.json_response({"ok": True, "data": data})


@web.middleware
async def auth_mw(request: web.Request, handler):
    if not request.path.startswith("/api/"):
        return await handler(request)
    user = validate_init_data(request.headers.get("X-Init-Data", ""), settings.bot_token)
    if not user:
        return _err("Avtorizatsiya xatosi. Kabinetni Telegram ichidan oching.", 401)
    uid = int(user["id"])
    if not _limiter.allow(uid):
        return _err("Juda ko‘p so‘rov. Biroz kuting.", 429)
    try:
        if not await is_subscribed(request.app["bot"], uid):
            return _err("Avval @o11abu kanaliga obuna bo‘ling.", 403)
    except SubscriptionError:
        return _err("Obunani tekshirib bo‘lmadi. Keyinroq urinib ko‘ring.", 503)
    await repo.upsert_user(uid, user.get("username"), user.get("first_name"))
    request["uid"] = uid
    return await handler(request)


def _hist_json(it: dict, full: bool = True) -> dict:
    out = {k: it[k] for k in ("id", "result_type", "reel_url", "hashtags", "video_date", "views",
                               "metric_label", "source", "direction", "created_at")}
    cap = it.get("caption") or ""
    out["caption"] = cap if full else cap[:140]
    return out


async def hashtag_load(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        url = str(body.get("url", ""))[:300]
    except Exception:
        return _err("So‘rov formati noto‘g‘ri.")
    uid = request["uid"]
    try:
        res = await get_reel_caption(url, ig)
        await repo.log_api("reel_caption", True)
    except SourceError as e:
        await repo.log_api("reel_caption", False, str(e))
        return _err(str(e), 422)
    except Exception:
        logger.exception("hashtag_load")
        await repo.log_api("reel_caption", False, "exception")
        return _err("Kutilmagan xato. Qayta urinib ko‘ring.", 500)
    hid = await repo.add_history(uid, "reel_caption", res.caption, res.hashtags, res.url,
                                 res.video_date, res.views, "ko‘rishlar" if res.views else None, res.source)
    await repo.bump("hashtag_load")
    return _ok({"id": hid, "url": res.url, "caption": res.caption, "hashtags": res.hashtags,
                "video_date": res.video_date, "views": res.views, "source": res.source})


async def bio_load(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        raw = str(body.get("username", ""))[:200]
    except Exception:
        return _err("So‘rov formati noto‘g‘ri.")
    try:
        p = await get_bio(raw, ig)
        await repo.log_api("bio", True)
    except SourceError as e:
        await repo.log_api("bio", False, str(e))
        return _err(str(e), 422)
    except Exception:
        logger.exception("bio_load")
        return _err("Kutilmagan xato. Qayta urinib ko‘ring.", 500)
    await repo.add_bio(request["uid"], p.username, p.name, p.biography, p.url, p.source)
    return _ok({"username": p.username, "name": p.name, "biography": p.biography, "url": p.url,
                "source": p.source})


async def history_list(request: web.Request) -> web.Response:
    try:
        offset = max(0, int(request.query.get("offset", 0)))
        limit = min(30, max(1, int(request.query.get("limit", 10))))
    except ValueError:
        return _err("Noto‘g‘ri parametr.")
    items, total = await repo.list_history(request["uid"], offset, limit)
    return _ok({"items": [_hist_json(i, full=False) for i in items], "total": total,
                "has_more": offset + len(items) < total})


async def history_get(request: web.Request) -> web.Response:
    try:
        item = await repo.get_history(request["uid"], int(request.match_info["id"]))
    except ValueError:
        return _err("Noto‘g‘ri id.")
    return _ok(_hist_json(item)) if item else _err("Topilmadi.", 404)


async def history_delete(request: web.Request) -> web.Response:
    try:
        ok = await repo.delete_history(request["uid"], int(request.match_info["id"]))
    except ValueError:
        return _err("Noto‘g‘ri id.")
    return _ok({"deleted": True}) if ok else _err("Topilmadi.", 404)


async def history_save(request: web.Request) -> web.Response:
    try:
        hid = int(request.match_info["id"])
    except ValueError:
        return _err("Noto‘g‘ri id.")
    if not await repo.get_history(request["uid"], hid):
        return _err("Topilmadi.", 404)
    await repo.save_item(request["uid"], hid, "cabinet")
    return _ok({"saved": True})


async def health(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def index(_: web.Request) -> web.FileResponse:
    return web.FileResponse(settings.webapp_dir / "index.html", headers={"Cache-Control": "no-cache"})


def create_app(bot) -> web.Application:
    app = web.Application(middlewares=[auth_mw])
    app["bot"] = bot
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_post("/api/hashtag", hashtag_load)
    app.router.add_post("/api/bio", bio_load)
    app.router.add_get("/api/history", history_list)
    app.router.add_get("/api/history/{id}", history_get)
    app.router.add_delete("/api/history/{id}", history_delete)
    app.router.add_post("/api/history/{id}/save", history_save)
    app.router.add_static("/src", settings.webapp_dir / "src")
    return app
