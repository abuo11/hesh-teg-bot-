from __future__ import annotations

import json
import re
from dataclasses import dataclass

import aiohttp

from bot.config import Settings, settings as default_settings
from bot.services.directions import Direction
from bot.utils.logger import logger
from bot.utils.validators import clean_tag

LANGS = {"uz": "o‘zbek", "ru": "rus", "en": "ingliz"}
STYLES = {"fun": "qiziqarli va yengil", "serious": "jiddiy va ishonchli",
          "motiv": "ilhomlantiruvchi", "short": "juda qisqa va lo‘nda"}
NOTE = "AI tomonidan yaratilgan tavsiya. Bu real trend ma’lumoti emas va natija kafolatlanmaydi."


@dataclass
class GenResult:
    caption: str
    hashtags: list[str]
    note: str
    engine: str  # "gemini" | "local"


def _norm_tags(tags: list[str], count: int) -> list[str]:
    out, seen = [], set()
    for t in tags:
        c = clean_tag(t)
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out[:count]


def local_generate(d: Direction, topic: str, lang: str, style: str, count: int) -> GenResult:
    words = [w for w in re.split(r"\s+", topic or "") if len(w) > 2][:6]
    topic_tags = [clean_tag(w) for w in words]
    tags = _norm_tags(topic_tags + list(d.fallback_tags), count)
    t = (topic or d.name).strip()
    caption = {
        "uz": f"{t} — buni oxirigacha ko‘ring 👀",
        "ru": f"{t} — смотри до конца 👀",
        "en": f"{t} — watch till the end 👀",
    }.get(lang, f"{t} 👀")
    return GenResult(caption, tags, NOTE, "local")


async def generate(d: Direction, topic: str = "", lang: str = "uz", style: str = "fun", count: int = 15,
                   cfg: Settings | None = None, session: aiohttp.ClientSession | None = None) -> GenResult:
    cfg = cfg or default_settings
    count = max(5, min(30, count))
    if not cfg.gemini_key:
        return local_generate(d, topic, lang, style, count)
    prompt = (
        "Sen Instagram Reels uchun SMM yordamchisan. Quyidagi ma'lumot bo'yicha ORIGINAL caption va "
        f"{count} ta hashtag yarat. Yo'nalish: {d.name}. Mavzu: {topic or 'umumiy'}. "
        f"Til: {LANGS.get(lang, 'o‘zbek')}. Uslub: {STYLES.get(style, 'qiziqarli')}. "
        "Caption 1-2 qisqa gap bo'lsin. Faqat JSON qaytar: "
        '{"caption": "...", "hashtags": ["#a", "#b"]}. Natija kafolati haqida yozma.'
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{cfg.gemini_model}:generateContent"
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9}}
    own = session is None
    sess = session or aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=25))
    try:
        async with sess.post(url, json=body, headers={"x-goog-api-key": cfg.gemini_key}) as r:
            data = await r.json(content_type=None)
            if r.status >= 400:
                raise RuntimeError(f"Gemini {r.status}")
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        obj = json.loads(re.sub(r"^```(?:json)?|```$", "", text.strip()).strip())
        tags = _norm_tags(obj.get("hashtags", []), count)
        if not tags:
            raise ValueError("bo'sh hashtag")
        return GenResult(str(obj.get("caption", "")).strip(), tags, NOTE, "gemini")
    except Exception as e:  # tarmoq, kvota, JSON — barchasida zaxira generator
        logger.warning("Gemini ishlamadi, lokal generator: %s", e.__class__.__name__)
        res = local_generate(d, topic, lang, style, count)
        res.note = NOTE + " (AI xizmati vaqtincha ishlamadi — oddiy generator ishlatildi.)"
        return res
    finally:
        if own:
            await sess.close()
