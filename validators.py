from __future__ import annotations

import re

_REEL = re.compile(
    r"^https?://(?:www\.)?instagram\.com/(?:[A-Za-z0-9_.]+/)?(reels?|p|tv)/([A-Za-z0-9_-]{5,})/?(?:\?.*)?$"
)
_USER = re.compile(r"^[A-Za-z0-9._]{1,30}$")
_PROFILE = re.compile(r"^https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]{1,30})/?(?:\?.*)?$")
_RESERVED = {"reel", "reels", "p", "tv", "stories", "explore", "accounts", "direct"}


def parse_reel_url(text: str) -> tuple[str, str] | None:
    """(normallashgan_url, shortcode) yoki None."""
    m = _REEL.match((text or "").strip())
    if not m:
        return None
    kind = "reel" if m.group(1).startswith("reel") else m.group(1)
    code = m.group(2)
    return f"https://www.instagram.com/{kind}/{code}/", code


def parse_username(text: str) -> str | None:
    t = (text or "").strip()
    m = _PROFILE.match(t)
    if m:
        t = m.group(1)
    t = t.lstrip("@")
    if t.lower() in _RESERVED or not _USER.match(t):
        return None
    return t.lower()


_TAG = re.compile(r"#[^\s#.,;:!?()\[\]{}<>\"']+", re.UNICODE)


def extract_hashtags(text: str) -> list[str]:
    seen, out = set(), []
    for t in _TAG.findall(text or ""):
        k = t.lower()
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out


def strip_hashtags(text: str) -> str:
    return re.sub(r"\s+", " ", _TAG.sub("", text or "")).strip()


def clean_tag(word: str) -> str:
    w = re.sub(r"[^\w]", "", word, flags=re.UNICODE)
    return f"#{w.lower()}" if w else ""
