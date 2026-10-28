import html
import logging
import re
from datetime import datetime, timedelta, timezone

FOOTER = "\n\n\nТг канал : @o11abu"
HASHTAG_RE = re.compile(r"#(\w+)", re.UNICODE)
REEL_RE = re.compile(
    r"^https?://(?:www\.)?instagram\.com/(?:[A-Za-z0-9._]+/)?(reel|reels|p|tv)/([A-Za-z0-9_-]+)/?(?:\?.*)?$"
)
USER_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")

DIRS = [
    ("🎬", "Kino", ["kino", "movie"]),
    ("🧸", "Multfilm", ["multfilm", "cartoon"]),
    ("🤖", "AI — sun’iy intellekt", ["ai", "chatgpt"]),
    ("😂", "Vayn", ["vayn", "funny"]),
    ("🏫", "School", ["school", "maktab"]),
    ("🙋", "Shaxsiy blog", ["blog", "vlog"]),
    ("🕌", "Arabic", ["arabic", "arab"]),
    ("🎵", "Musiqa", ["musiqa", "music"]),
    ("⭐", "Fan club", ["fanclub", "fanpage"]),
    ("☪️", "Islomiy kontent", ["islom", "islamic"]),
    ("📱", "iMovie videolar", ["imovie", "videoedit"]),
    ("❤️", "Love — sevgi", ["love", "sevgi"]),
    ("📸", "Stories", ["stories", "storyvideo"]),
    ("✂️", "Edit", ["edit", "edits"]),
    ("⚽", "Futbol", ["futbol", "football"]),
    ("🎁", "Atalgan videolar", ["atalgan", "tribute"]),
]


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def esc(s) -> str:
    return html.escape(str(s or ""))


def split_text(text: str, limit: int = 3800) -> list[str]:
    parts, cur = [], ""
    for line in text.split("\n"):
        while len(line) > limit:
            if cur:
                parts.append(cur)
                cur = ""
            parts.append(line[:limit])
            line = line[limit:]
        if len(cur) + len(line) + 1 > limit:
            parts.append(cur)
            cur = line
        else:
            cur = f"{cur}\n{line}" if cur else line
    if cur:
        parts.append(cur)
    return parts or [""]


def extract_hashtags(text: str) -> list[str]:
    seen, out = set(), []
    for t in HASHTAG_RE.findall(text or ""):
        k = t.lower()
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def tags_line(tags) -> str:
    return " ".join("#" + t.lstrip("#") for t in tags)


def full_text(caption: str, tags) -> str:
    parts = [p for p in ((caption or "").strip(), tags_line(tags)) if p]
    return "\n\n".join(parts) + FOOTER


def valid_reel_url(url: str):
    m = REEL_RE.match((url or "").strip())
    return m.group(2) if m else None


def valid_username(raw: str):
    s = (raw or "").strip()
    m = re.match(r"^https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]+)/?(?:\?.*)?$", s)
    if m:
        s = m.group(1)
    s = s.lstrip("@")
    return s if USER_RE.match(s) else None


def parse_ts(s):
    if not s:
        return None
    for f in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
        try:
            return datetime.strptime(s, f)
        except ValueError:
            pass
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def within_days(ts, days: int = 7, now=None) -> bool:
    """Aniq oxirgi days*24 soat ichidami (hozirdan orqaga)."""
    d = ts if isinstance(ts, datetime) else parse_ts(ts)
    if d is None:
        return False
    now = now or datetime.now(timezone.utc)
    return now - timedelta(days=days) <= d <= now + timedelta(minutes=5)


def fmt_dt(ts) -> str:
    d = ts if isinstance(ts, datetime) else parse_ts(ts)
    return d.strftime("%d.%m.%Y %H:%M") if d else "—"
