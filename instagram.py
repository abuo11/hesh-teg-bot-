"""Instagram ma'lumot manbasi (faqat rasmiy Graph API). Hech narsa o'ylab topilmaydi."""
import logging

import aiohttp

from ..config import cfg
from .. import db
from ..utils import extract_hashtags, valid_reel_url, within_days

log = logging.getLogger(__name__)
GRAPH = "https://graph.facebook.com/v21.0"
MEDIA_FIELDS = "id,caption,media_type,permalink,timestamp,like_count,comments_count"
_hid_cache: dict[str, str] = {}


class IGError(Exception):
    """Foydalanuvchiga ko'rsatiladigan xatolik."""


def configured() -> bool:
    return bool(cfg.ig_token and cfg.ig_user_id)


async def _get(path: str, params: dict) -> dict:
    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get(f"{GRAPH}/{path}", params=params) as r:
                data = await r.json(content_type=None)
    except Exception as e:
        await db.log_api("instagram", f"tarmoq: {type(e).__name__}")
        raise IGError("Instagram serveriga ulanib bo‘lmadi. Birozdan keyin urinib ko‘ring.")
    if isinstance(data, dict) and "error" in data:
        err = data["error"]
        await db.log_api("instagram", f"{err.get('code')}: {str(err.get('message'))[:200]}")
        raise IGError(f"Instagram API xatosi: {str(err.get('message', ''))[:160]}")
    return data


def _pack(it: dict, source: str, url: str | None = None) -> dict:
    caption = it.get("caption") or ""
    return {
        "url": url or it.get("permalink", ""),
        "caption": caption,
        "hashtags": extract_hashtags(caption),
        "posted_at": it.get("timestamp"),
        "views": None,  # hashtag/media endpointlari ko'rishlar sonini bermaydi
        "likes": it.get("like_count"),
        "comments": it.get("comments_count"),
        "source": source,
    }


async def fetch_reel(url: str) -> dict:
    code = valid_reel_url(url)
    if not code:
        raise IGError("Havola noto‘g‘ri. Namuna: https://www.instagram.com/reel/XXXX/")
    if not configured() and not cfg.oembed_token:
        raise IGError("Instagram ma’lumot manbasi sozlanmagan (README, 7-bo‘lim).")

    # 1) O'z akkauntingiz Reelslari (caption to'liq qaytadi)
    if configured():
        after = None
        for _ in range(4):
            params = {"fields": MEDIA_FIELDS, "limit": 50, "access_token": cfg.ig_token}
            if after:
                params["after"] = after
            data = await _get(f"{cfg.ig_user_id}/media", params)
            for it in data.get("data", []):
                if code in (it.get("permalink") or ""):
                    if not it.get("caption"):
                        raise IGError("Bu videoda caption yo‘q.")
                    return _pack(it, "Instagram Graph API (o‘z akkaunt)", url)
            paging = data.get("paging", {})
            after = paging.get("cursors", {}).get("after")
            if not paging.get("next"):
                break

    # 2) oEmbed (boshqa akkauntlar uchun caption qaytishi kafolatlanmaydi)
    if cfg.oembed_token:
        data = await _get("instagram_oembed", {"url": url, "omitscript": "true",
                                               "access_token": cfg.oembed_token})
        caption = data.get("title") or ""
        if caption:
            return _pack({"caption": caption, "permalink": url}, "Instagram oEmbed", url)

    raise IGError("Bu havola uchun caption olinmadi. Instagram rasmiy API’si boshqa "
                  "akkaunt videolarining captionini odatda bermaydi. Faqat o‘z akkauntingiz "
                  "(sozlangan) Reelslari uchun ishlaydi.")


async def _hashtag_id(tag: str) -> str | None:
    if tag in _hid_cache:
        return _hid_cache[tag]
    d = await _get("ig_hashtag_search", {"user_id": cfg.ig_user_id, "q": tag,
                                         "access_token": cfg.ig_token})
    if d.get("data"):
        _hid_cache[tag] = d["data"][0]["id"]
        return _hid_cache[tag]
    return None


async def top_videos(tags: list[str], limit: int = 3, days: int = 7) -> list[dict]:
    """Oxirgi `days` kun ichidagi videolardan layk+izoh bo'yicha TOP."""
    if not configured():
        raise IGError("TOP tahlil uchun Instagram Graph API (IG_ACCESS_TOKEN va IG_USER_ID) "
                      "sozlanishi kerak. README, 7-bo‘lim.")
    found: dict[str, dict] = {}
    for tag in tags[:2]:  # haftasiga 30 ta noyob hashtag limiti uchun tejaymiz
        hid = await _hashtag_id(tag)
        if not hid:
            continue
        for edge in ("top_media", "recent_media"):
            d = await _get(f"{hid}/{edge}", {"user_id": cfg.ig_user_id, "fields": MEDIA_FIELDS,
                                              "limit": 50, "access_token": cfg.ig_token})
            for it in d.get("data", []):
                if it.get("media_type") != "VIDEO":
                    continue
                if not within_days(it.get("timestamp"), days):
                    continue
                found[it["id"]] = it
    ranked = sorted(found.values(),
                    key=lambda x: (x.get("like_count") or 0) + (x.get("comments_count") or 0),
                    reverse=True)
    return [_pack(it, "Instagram Graph API (hashtag qidiruvi)") for it in ranked[:limit]]


async def fetch_bio(username: str) -> dict:
    if not configured():
        raise IGError("Bio olish uchun Instagram Graph API sozlanishi kerak (README, 7-bo‘lim).")
    fields = ("business_discovery.username(%s){username,name,biography,website,"
              "profile_picture_url}" % username)
    d = await _get(cfg.ig_user_id, {"fields": fields, "access_token": cfg.ig_token})
    bd = d.get("business_discovery")
    if not bd:
        raise IGError("Profil topilmadi yoki u business/creator akkaunt emas.")
    return {"username": bd.get("username", username), "name": bd.get("name", ""),
            "bio": bd.get("biography", ""),
            "profile_url": f"https://www.instagram.com/{bd.get('username', username)}/",
            "source": "Instagram Graph API (Business Discovery)"}
