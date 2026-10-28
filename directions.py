from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Direction:
    key: str
    emoji: str
    name: str
    seed_tags: tuple[str, ...]      # Graph API hashtag qidiruvi uchun
    keywords: tuple[str, ...]       # yo'nalishga moslikni tekshirish uchun
    fallback_tags: tuple[str, ...]  # AI ishlamasa ishlatiladigan asosiy teglar


DIRECTIONS: list[Direction] = [
    Direction("kino", "🎬", "Kino", ("kino", "movie"), ("kino", "film", "movie", "cinema", "serial"),
              ("#kino", "#film", "#movie", "#cinema", "#kinolar", "#uzbekkino", "#reels", "#trend")),
    Direction("multfilm", "🧸", "Multfilm", ("multfilm", "cartoon"), ("multfilm", "cartoon", "animation", "anime"),
              ("#multfilm", "#cartoon", "#animation", "#bolalar", "#reels", "#fyp")),
    Direction("ai", "🤖", "AI — sun’iy intellekt", ("ai", "artificialintelligence"),
              ("ai", "chatgpt", "neural", "sun'iy", "intellekt", "artificialintelligence"),
              ("#ai", "#sunyiyintellekt", "#chatgpt", "#aitools", "#technology", "#future", "#reels")),
    Direction("vayn", "😂", "Vayn", ("vine", "vayn", "comedy"), ("vine", "vayn", "comedy", "funny", "kulgu"),
              ("#vayn", "#vine", "#comedy", "#funny", "#kulgu", "#reels", "#fyp")),
    Direction("school", "🏫", "School — sinf akkauntlari", ("school", "maktab"),
              ("school", "maktab", "sinf", "class", "student"),
              ("#school", "#maktab", "#sinf", "#classmates", "#students", "#reels")),
    Direction("blog", "🙋", "Shaxsiy blog", ("blogger", "vlog"), ("blog", "vlog", "kunlik", "daily"),
              ("#blog", "#blogger", "#vlog", "#dailyvlog", "#lifestyle", "#reels")),
    Direction("arabic", "🕌", "Arabic", ("arabic", "arab"), ("arab", "arabic", "عرب"),
              ("#arabic", "#arab", "#arabicmusic", "#arabiccontent", "#reels")),
    Direction("musiqa", "🎵", "Musiqa", ("music", "musiqa"), ("music", "musiqa", "song", "qo'shiq", "qoshiq"),
              ("#musiqa", "#music", "#song", "#qoshiq", "#newmusic", "#reels", "#fyp")),
    Direction("fanclub", "⭐", "Fan club", ("fanclub", "fanpage"), ("fan", "fanclub", "fanpage"),
              ("#fanclub", "#fanpage", "#fans", "#edit", "#reels")),
    Direction("islom", "🕋", "Islomiy kontent", ("islam", "islomiy"),
              ("islam", "islom", "namoz", "quran", "qur'on", "ma'ruza", "dua"),
              ("#islom", "#islam", "#namoz", "#quran", "#duo", "#islomiy", "#reels")),
    Direction("imovie", "🎞", "iMovie videolar", ("imovie", "iphoneedit"), ("imovie", "iphone", "edit"),
              ("#imovie", "#iphoneedit", "#videoedit", "#reels", "#montage")),
    Direction("love", "❤️", "Love — sevgi", ("love", "sevgi"), ("love", "sevgi", "muhabbat", "romantic"),
              ("#love", "#sevgi", "#muhabbat", "#romantic", "#lovestory", "#reels")),
    Direction("stories", "📱", "Stories", ("story", "storyvideo"), ("story", "stories", "istoriya"),
              ("#stories", "#story", "#storyvideo", "#instastory", "#reels")),
    Direction("edit", "✂️", "Edit", ("edit", "videoedit"), ("edit", "capcut", "montage"),
              ("#edit", "#videoedit", "#capcut", "#editing", "#reels", "#fyp")),
    Direction("futbol", "⚽", "Futbol", ("football", "futbol"),
              ("football", "futbol", "goal", "gol", "transfer", "soccer"),
              ("#futbol", "#football", "#gol", "#goals", "#transfer", "#soccer", "#reels")),
    Direction("atalgan", "🎁", "Atalgan videolar", ("forher", "forhim"),
              ("for", "uchun", "sevgan", "tugilgan", "birthday", "tabrik"),
              ("#foryou", "#tabrik", "#birthday", "#sevgilim", "#dostim", "#reels")),
]


def get_direction(idx: int) -> Direction:
    return DIRECTIONS[idx]
