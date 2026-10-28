"""Instagram ma'lumot manbasi (alohida modul).

Faqat RASMIY Meta endpointlari ishlatiladi:
  * Instagram oEmbed (Meta oEmbed Read)  -> INSTAGRAM_OEMBED_TOKEN
  * Instagram Graph API (Business/Creator akkaunt) -> INSTAGRAM_USER_ID + INSTAGRAM_ACCESS_TOKEN
Hech qanday scraping yoki login ishlatilmaydi. Ma'lumot bo'lmasa SourceError qaytadi.
"""
from __future__ import annotations

import html as htmllib
import re
from dataclasses import dataclass, field
from datetime import datetime

import aiohttp

from bot.config import Settings, settings as default_settings
from bot.utils.time_utils import parse_ts
from bot.utils.validators import extract_hashtags

GRAPH = "https://graph.facebook.com/v21.0"
TIMEOUT = aiohttp.ClientTimeout(total=20)


class SourceError(Exception):
    """Foydalanuvchiga ko'rsatiladigan tushunarli xato."""


@dataclass
class MediaItem:
    url: str
    caption: str = ""
    timestamp: datetime | None = None
    media_type: str = ""
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    thumbnail: str | None = None
    source: str = ""
    hashtags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.hashtags:
            self.hashtags = extract_hashtags(self.caption)


@dataclass
class Profile:
    username: str
    name: str
    biography: str
    url: str
    source: str


class InstagramAPI:
    def __init__(self, cfg: Settings | None = None, session: aiohttp.ClientSession | None = None):
        self.cfg = cfg or default_settings
        self._session = session

    async def _get(self, url: str, params: dict) -> dict:
        own = self._session is None
        sess = self._session or aiohttp.ClientSession(timeout=TIMEOUT)
        try:
            async with sess.get(url, params=params) as resp:
                data = await resp.json(content_type=None)
                if resp.status >= 400:
                    err = (data or {}).get("error", {}) if isinstance(data, dict) else {}
                    raise SourceError(f"Instagram API xatosi ({resp.status}): {err.get('message', 'noma’lum xato')}")
                return data
        except aiohttp.ClientError as e:
            raise SourceError(f"Instagram API bilan aloqa o‘rnatilmadi: {e.__class__.__name__}") from e
        except TimeoutError as e:
            raise SourceError("Instagram API javob bermadi (timeout).") from e
        finally:
            if own:
                await sess.close()

    # ---------------- Reels / post ----------------
    async def fetch_reel(self, url: str, shortcode: str) -> MediaItem:
        errors: list[str] = []
        if self.cfg.ig_user_id and self.cfg.ig_access_token:
            try:
                item = await self._own_media(shortcode)
                if item:
                    return item
                errors.append("Bu video ulangan Instagram akkauntga tegishli emas.")
            except SourceError as e:
                errors.append(str(e))
        if self.cfg.ig_oembed_token:
            try:
                return await self._oembed(url)
            except SourceError as e:
                errors.append(str(e))
        if not errors:
            raise SourceError(
                "Instagram ma’lumot manbasi sozlanmagan. .env faylida INSTAGRAM_OEMBED_TOKEN yoki "
                "INSTAGRAM_USER_ID/INSTAGRAM_ACCESS_TOKEN ni kiriting (README ga qarang)."
            )
        raise SourceError(" ".join(errors))

    async def _own_media(self, shortcode: str) -> MediaItem | None:
        params = {
            "fields": "id,caption,media_type,permalink,timestamp,like_count,comments_count,thumbnail_url",
            "limit": 50, "access_token": self.cfg.ig_access_token,
        }
        url = f"{GRAPH}/{self.cfg.ig_user_id}/media"
        for _ in range(4):  # eng ko'pi bilan 200 ta oxirgi media
            data = await self._get(url, params)
            for m in data.get("data", []):
                if shortcode in (m.get("permalink") or ""):
                    return self._to_item(m, "Instagram Graph API")
            nxt = (data.get("paging") or {}).get("next")
            if not nxt:
                break
            url, params = nxt, {}
        return None

    async def _oembed(self, url: str) -> MediaItem:
        data = await self._get(f"{GRAPH}/instagram_oembed",
                               {"url": url, "access_token": self.cfg.ig_oembed_token, "omitscript": "true"})
        caption = (data.get("title") or "").strip()
        if not caption and data.get("html"):
            caption = self._caption_from_embed(data["html"])
        if not caption:
            raise SourceError("oEmbed bu havola uchun caption qaytarmadi (Instagram ruxsat bermagan bo‘lishi mumkin).")
        return MediaItem(url=url, caption=caption, thumbnail=data.get("thumbnail_url"), source="Instagram oEmbed")

    @staticmethod
    def _caption_from_embed(embed_html: str) -> str:
        m = re.search(r"<blockquote.*?</blockquote>", embed_html, re.S)
        if not m:
            return ""
        text = re.sub(r"<(script|style).*?</\1>", "", m.group(0), flags=re.S)
        text = re.sub(r"<[^>]+>", "\n", text)
        lines = [htmllib.unescape(l).strip() for l in text.split("\n") if l.strip()]
        lines = [l for l in lines if not l.lower().startswith(("view this", "a post shared", "a video shared"))]
        return " ".join(lines[:1]) if lines else ""

    # ---------------- Bio ----------------
    async def fetch_profile(self, username: str) -> Profile:
        if not (self.cfg.ig_user_id and self.cfg.ig_access_token):
            raise SourceError(
                "Bio olish uchun INSTAGRAM_USER_ID va INSTAGRAM_ACCESS_TOKEN kerak (Business/Creator akkaunt)."
            )
        fields = f"business_discovery.username({username}){{username,name,biography,website}}"
        data = await self._get(f"{GRAPH}/{self.cfg.ig_user_id}",
                               {"fields": fields, "access_token": self.cfg.ig_access_token})
        bd = data.get("business_discovery")
        if not bd:
            raise SourceError("Profil topilmadi.")
        return Profile(
            username=bd.get("username", username), name=bd.get("name", ""),
            biography=bd.get("biography", ""), url=f"https://www.instagram.com/{username}/",
            source="Instagram Graph API (business_discovery)",
        )

    # ---------------- Hashtag media ----------------
    async def hashtag_media(self, tag: str) -> list[MediaItem]:
        if not (self.cfg.ig_user_id and self.cfg.ig_access_token):
            raise SourceError("TOP videolar uchun INSTAGRAM_USER_ID va INSTAGRAM_ACCESS_TOKEN kerak.")
        base = {"user_id": self.cfg.ig_user_id, "access_token": self.cfg.ig_access_token}
        found = await self._get(f"{GRAPH}/ig_hashtag_search", {**base, "q": tag})
        ids = found.get("data") or []
        if not ids:
            return []
        hid = ids[0]["id"]
        fields = "id,caption,media_type,permalink,timestamp,like_count,comments_count"
        items: dict[str, MediaItem] = {}
        for edge in ("top_media", "recent_media"):
            data = await self._get(f"{GRAPH}/{hid}/{edge}", {**base, "fields": fields, "limit": 50})
            for m in data.get("data", []):
                it = self._to_item(m, f"Instagram Graph API (#{tag})")
                items[it.url] = it
        return list(items.values())

    @staticmethod
    def _to_item(m: dict, source: str) -> MediaItem:
        views = m.get("video_view_count") or m.get("play_count")
        return MediaItem(
            url=m.get("permalink", ""), caption=m.get("caption") or "",
            timestamp=parse_ts(m.get("timestamp")), media_type=m.get("media_type", ""),
            views=int(views) if views is not None else None,
            likes=m.get("like_count"), comments=m.get("comments_count"),
            thumbnail=m.get("thumbnail_url"), source=source,
        )
