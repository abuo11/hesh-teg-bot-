from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from bot.services.directions import Direction
from bot.services.instagram_api import InstagramAPI, MediaItem, SourceError
from bot.utils.time_utils import now_utc, within_7_days

MAX_SEED_TAGS = 2  # Graph API: 7 kunda 30 ta noyob hashtag limiti


@dataclass
class TopResult:
    items: list[MediaItem]
    metric_label: str          # "ko‘rishlar" yoki "layklar"
    scanned: int
    note: str


def _is_video(m: MediaItem) -> bool:
    return m.media_type.upper() in ("VIDEO", "REELS", "REEL")


def _fits(m: MediaItem, d: Direction) -> bool:
    hay = (m.caption + " " + " ".join(m.hashtags)).lower()
    return any(k in hay for k in d.keywords)


def pick_top3(items: list[MediaItem], d: Direction, now: datetime | None = None) -> TopResult:
    """Sana filtri -> yo'nalishga moslik -> saralash -> TOP-3. Sof funksiya (testlanadi)."""
    now = now or now_utc()
    seen, pool = set(), []
    for m in items:
        if not m.url or m.url in seen:
            continue
        seen.add(m.url)
        if _is_video(m) and within_7_days(m.timestamp, now) and _fits(m, d):
            pool.append(m)
    if any(m.views is not None for m in pool):
        label = "ko‘rishlar"
        pool = [m for m in pool if m.views is not None]
        pool.sort(key=lambda m: m.views or 0, reverse=True)
    else:
        label = "layklar"
        pool = [m for m in pool if m.likes is not None]
        pool.sort(key=lambda m: m.likes or 0, reverse=True)
    note = ("Tekshirilgan videolar orasidagi TOP-3. " +
            ("" if label == "ko‘rishlar" else
             "Instagram hashtag API ko‘rishlar sonini bermaydi, shuning uchun reyting layklar bo‘yicha."))
    return TopResult(items=pool[:3], metric_label=label, scanned=len(seen), note=note.strip())


async def top_videos(api: InstagramAPI, d: Direction) -> TopResult:
    collected: list[MediaItem] = []
    last_err: SourceError | None = None
    for tag in d.seed_tags[:MAX_SEED_TAGS]:
        try:
            collected.extend(await api.hashtag_media(tag))
        except SourceError as e:
            last_err = e
    if not collected and last_err:
        raise last_err
    return pick_top3(collected, d)
