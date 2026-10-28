import pytest

from bot.database.repository import Repository
from bot.database.session import Database


@pytest.fixture
def repo():
    return Repository(Database(":memory:"))


async def test_auto_history_and_isolation(repo):
    a = await repo.add_history(1, "reel_caption", "cap A", ["#a"], "https://x/reel/aaaaa/")
    await repo.add_history(2, "ai_generated", "cap B", ["#b"])
    items, total = await repo.list_history(1)
    assert total == 1 and items[0]["caption"] == "cap A" and items[0]["hashtags"] == ["#a"]
    assert await repo.get_history(2, a) is None          # boshqa foydalanuvchi ko'ra olmaydi


async def test_delete_only_own(repo):
    a = await repo.add_history(1, "top3", "x", [])
    assert not await repo.delete_history(2, a)
    assert await repo.delete_history(1, a)
    assert (await repo.list_history(1))[1] == 0


async def test_pagination(repo):
    for i in range(25):
        await repo.add_history(1, "ai_generated", f"c{i}", [])
    first, total = await repo.list_history(1, 0, 10)
    last, _ = await repo.list_history(1, 20, 10)
    assert total == 25 and len(first) == 10 and len(last) == 5 and first[0]["caption"] == "c24"


async def test_tables_exist_and_stats(repo):
    for t in ("users", "hashtag_history", "video_analysis_history", "saved_items", "api_logs",
              "bot_statistics", "bio_history"):
        assert repo.db.one("SELECT name FROM sqlite_master WHERE name=?", (t,))
    await repo.upsert_user(5, "u", "U")
    await repo.log_api("src", False, "err")
    await repo.bump("top")
    s = await repo.stats()
    assert s["users_total"] == 1 and s["api_errors_7d"] == 1 and s["top_total"] == 1
