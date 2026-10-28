import json
import logging
import re

import aiohttp

from ..config import cfg
from .. import db
from ..utils import DIRS

log = logging.getLogger(__name__)
LANGS = {"uz": "o‘zbek", "ru": "rus", "en": "ingliz"}


def _clean(tags, count):
    out, seen = [], set()
    for t in tags:
        t = re.sub(r"[^\w]", "", str(t).lstrip("#"), flags=re.UNICODE).lower()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out[:count]


async def _gemini(direction, topic, lang, style, count):
    prompt = (
        f"Instagram Reels uchun original caption va {count} ta hashtag yarat.\n"
        f"Yo'nalish: {direction}. Mavzu: {topic}. Til: {LANGS.get(lang, 'o‘zbek')}. "
        f"Uslub: {style}.\nFaqat JSON qaytar: "
        '{"caption": "...", "hashtags": ["..."], "note": "qisqa izoh"}. '
        "Hashtaglarda # belgisi va bo'sh joy bo'lmasin. Kafolat va'da qilma.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{cfg.gemini_model}:generateContent"
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9}}
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.post(url, json=body, headers={"x-goog-api-key": cfg.gemini_key}) as r:
            data = await r.json(content_type=None)
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    j = json.loads(text)
    tags = _clean(j.get("hashtags", []), count)
    if not tags or not j.get("caption"):
        raise ValueError("bo'sh javob")
    return {"caption": str(j["caption"]).strip(), "hashtags": tags,
            "note": str(j.get("note", "")).strip(), "source": f"AI ({cfg.gemini_model})"}


def _fallback(direction, topic, lang, style, count):
    base = next((d[2] for d in DIRS if d[1] == direction), [])
    words = [w for w in re.findall(r"\w+", topic.lower(), flags=re.UNICODE) if len(w) > 3]
    generic = ["reels", "reelsuz", "trend", "fyp", "uzbekistan", "tavsiya"]
    tags = _clean(base + words + generic, count)
    caption = f"{topic.strip().capitalize()} ✨" if topic.strip() else f"{direction} ✨"
    return {"caption": caption, "hashtags": tags,
            "note": "Oflayn shablon: AI kaliti sozlanmagan, trend ma’lumoti ishlatilmadi.",
            "source": "Oflayn shablon"}


async def generate(direction, topic, lang="uz", style="qiziqarli", count=15) -> dict:
    count = max(5, min(int(count), 30))
    topic = (topic or direction).strip()[:300]
    res = None
    if cfg.gemini_key:
        try:
            res = await _gemini(direction, topic, lang, style, count)
        except Exception as e:
            log.warning("Gemini xatosi: %s", type(e).__name__)
            await db.log_api("gemini", f"{type(e).__name__}")
    if res is None:
        res = _fallback(direction, topic, lang, style, count)
    res["label"] = "AI tomonidan yaratilgan tavsiya (haqiqiy trend ma’lumoti emas)"
    return res
