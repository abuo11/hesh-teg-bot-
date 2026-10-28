from __future__ import annotations

from dataclasses import dataclass

from bot.services.instagram_api import InstagramAPI, SourceError
from bot.utils.time_utils import fmt_dt
from bot.utils.validators import parse_reel_url, strip_hashtags


@dataclass
class CaptionResult:
    url: str
    caption: str
    hashtags: list[str]
    video_date: str | None
    views: int | None
    source: str


async def get_reel_caption(raw_url: str, api: InstagramAPI) -> CaptionResult:
    parsed = parse_reel_url(raw_url)
    if not parsed:
        raise SourceError("Havola noto‘g‘ri. Namuna: https://www.instagram.com/reel/XXXXXXXX/")
    url, code = parsed
    item = await api.fetch_reel(url, code)
    if not item.caption and not item.hashtags:
        raise SourceError("Bu videoda caption yoki hashtag topilmadi.")
    return CaptionResult(
        url=item.url or url,
        caption=strip_hashtags(item.caption) or item.caption,
        hashtags=item.hashtags,
        video_date=fmt_dt(item.timestamp) if item.timestamp else None,
        views=item.views,
        source=item.source,
    )
