from datetime import datetime, timedelta, timezone

import pytest

from bot.services.directions import DIRECTIONS
from bot.services.hashtag_generator import generate
from bot.services.instagram_api import InstagramAPI, MediaItem, SourceError
from bot.services.trend_analyzer import pick_top3
from bot.utils.text_formatter import build_copy_text, split_message
from bot.utils.validators import extract_hashtags, parse_reel_url, parse_username
from bot.config import Settings

NOW = datetime(2026, 10, 27, 20, 0, tzinfo=timezone.utc)
FUT = DIRECTIONS[14]  # futbol


def mk(i, days, views=None, likes=None, cap="Futbol gol #futbol"):
    return MediaItem(url=f"https://instagram.com/reel/A{i}xxxx/", caption=cap, media_type="VIDEO",
                     timestamp=NOW - timedelta(days=days), views=views, likes=likes)


def test_16_directions():
    assert len(DIRECTIONS) == 16


def test_reel_url_validation():
    assert parse_reel_url("https://www.instagram.com/reel/Cabc123xyz/?igsh=1")[1] == "Cabc123xyz"
    assert parse_reel_url("https://example.com/reel/abc") is None
    assert parse_reel_url("salom") is None


def test_username_parsing():
    assert parse_username("@Some.User") == "some.user"
    assert parse_username("https://instagram.com/some_user/") == "some_user"
    assert parse_username("a b") is None
    assert parse_username("reel") is None


def test_hashtag_extraction_dedup():
    assert extract_hashtags("a #Gol #gol #futbol!") == ["#Gol", "#futbol"]


def test_top3_filters_old_and_sorts_by_views():
    items = [mk(1, 400, views=10_000_000), mk(2, 1, views=500), mk(3, 2, views=900), mk(4, 3, views=100),
             mk(5, 4, views=700)]
    res = pick_top3(items, FUT, NOW)
    assert [m.views for m in res.items] == [900, 700, 500]
    assert res.metric_label == "ko‘rishlar"


def test_top3_falls_back_to_likes_honestly():
    res = pick_top3([mk(1, 1, likes=5), mk(2, 2, likes=50)], FUT, NOW)
    assert res.metric_label == "layklar" and res.items[0].likes == 50
    assert "layk" in res.note


def test_top3_direction_fit_and_non_video():
    off = mk(1, 1, likes=99, cap="oshxona retsept")
    img = mk(2, 1, likes=99); img.media_type = "IMAGE"
    assert pick_top3([off, img], FUT, NOW).items == []


def test_copy_text_has_signature_after_two_blank_lines():
    t = build_copy_text("cap", ["#a"])
    assert t.endswith("\n\n\nТг канал : @o11abu")


def test_split_message_limit():
    parts = split_message("x" * 9000, 4000)
    assert all(len(p) <= 4000 for p in parts) and "".join(parts) == "x" * 9000


async def test_generator_local_fallback_marks_ai():
    r = await generate(FUT, "Messi goli", "uz", "fun", 10, cfg=Settings(gemini_key=""))
    assert r.engine == "local" and "AI tomonidan yaratilgan" in r.note and len(r.hashtags) <= 10
    assert "kafolat" in r.note.lower()


async def test_source_not_configured_raises_clear_error():
    api = InstagramAPI(Settings())
    with pytest.raises(SourceError):
        await api.fetch_reel("https://www.instagram.com/reel/Cabc123xyz/", "Cabc123xyz")
    with pytest.raises(SourceError):
        await api.fetch_profile("someone")
