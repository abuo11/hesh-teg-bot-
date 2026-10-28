from __future__ import annotations

import html

from bot.config import settings

TG_LIMIT = 4000


def esc(text: str | None) -> str:
    return html.escape(text or "")


def with_signature(text: str) -> str:
    """Tayyor matn oxiriga ikki qator bo'sh joy va kanal yozuvi."""
    return f"{text.rstrip()}\n\n\n{settings.signature}"


def build_copy_text(caption: str, hashtags: list[str]) -> str:
    parts = [p for p in (caption.strip(), " ".join(hashtags)) if p]
    return with_signature("\n\n".join(parts))


def split_message(text: str, limit: int = TG_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks, cur = [], ""
    for line in text.split("\n"):
        while len(line) > limit:
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(line[:limit])
            line = line[limit:]
        if len(cur) + len(line) + 1 > limit:
            chunks.append(cur)
            cur = line
        else:
            cur = f"{cur}\n{line}" if cur else line
    if cur:
        chunks.append(cur)
    return chunks


def short(text: str, n: int = 120) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def fmt_num(n: int | None) -> str:
    return f"{n:,}".replace(",", " ") if n is not None else "—"
