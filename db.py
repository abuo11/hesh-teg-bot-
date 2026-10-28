import json
import time
from datetime import datetime, timezone

import aiosqlite

from .config import cfg

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
  created_at REAL, last_seen REAL);
CREATE TABLE IF NOT EXISTS hashtag_history(
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, kind TEXT NOT NULL,
  url TEXT, caption TEXT, hashtags TEXT, source TEXT, posted_at TEXT,
  views INTEGER, likes INTEGER, direction TEXT, note TEXT, created_at REAL);
CREATE INDEX IF NOT EXISTS ix_hh_user ON hashtag_history(user_id, id DESC);
CREATE TABLE IF NOT EXISTS video_analysis_history(
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, direction TEXT,
  report TEXT, score REAL, created_at REAL);
CREATE TABLE IF NOT EXISTS saved_items(
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, history_id INTEGER,
  created_at REAL, UNIQUE(user_id, history_id));
CREATE TABLE IF NOT EXISTS bio_history(
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, username TEXT,
  name TEXT, bio TEXT, profile_url TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS api_logs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, error TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS bot_statistics(
  day TEXT, key TEXT, count INTEGER DEFAULT 0, PRIMARY KEY(day, key));
"""


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


async def _exec(sql, args=(), *, one=False, many=False):
    async with aiosqlite.connect(cfg.db_path) as con:
        con.row_factory = aiosqlite.Row
        cur = await con.execute(sql, args)
        if many:
            return [dict(r) for r in await cur.fetchall()]
        if one:
            r = await cur.fetchone()
            return dict(r) if r else None
        await con.commit()
        return cur.lastrowid


async def init() -> None:
    async with aiosqlite.connect(cfg.db_path) as con:
        await con.execute("PRAGMA journal_mode=WAL")
        await con.executescript(SCHEMA)
        await con.commit()


async def upsert_user(user_id, username, first_name) -> None:
    now = time.time()
    await _exec(
        "INSERT INTO users(user_id,username,first_name,created_at,last_seen) VALUES(?,?,?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, "
        "first_name=excluded.first_name, last_seen=excluded.last_seen",
        (user_id, username, first_name, now, now))


def _row(r):
    if r:
        try:
            r["hashtags"] = json.loads(r.get("hashtags") or "[]")
        except ValueError:
            r["hashtags"] = []
    return r


async def add_history(user_id, kind, *, url="", caption="", hashtags=(), source="",
                      posted_at=None, views=None, likes=None, direction="", note=""):
    return await _exec(
        "INSERT INTO hashtag_history(user_id,kind,url,caption,hashtags,source,posted_at,views,"
        "likes,direction,note,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (user_id, kind, url, caption, json.dumps(list(hashtags)), source, posted_at,
         views, likes, direction, note, time.time()))


async def get_history(user_id, hid):
    return _row(await _exec("SELECT * FROM hashtag_history WHERE id=? AND user_id=?",
                            (hid, user_id), one=True))


async def list_history(user_id, limit=10, offset=0):
    rows = await _exec("SELECT * FROM hashtag_history WHERE user_id=? ORDER BY id DESC "
                       "LIMIT ? OFFSET ?", (user_id, limit, offset), many=True)
    return [_row(r) for r in rows]


async def count_history(user_id) -> int:
    r = await _exec("SELECT COUNT(*) c FROM hashtag_history WHERE user_id=?", (user_id,), one=True)
    return r["c"]


async def delete_history(user_id, hid) -> bool:
    async with aiosqlite.connect(cfg.db_path) as con:
        cur = await con.execute("DELETE FROM hashtag_history WHERE id=? AND user_id=?",
                                (hid, user_id))
        await con.execute("DELETE FROM saved_items WHERE user_id=? AND history_id=?",
                          (user_id, hid))
        await con.commit()
        return cur.rowcount > 0


async def save_item(user_id, hid) -> bool:
    if not await get_history(user_id, hid):
        return False
    await _exec("INSERT OR IGNORE INTO saved_items(user_id,history_id,created_at) VALUES(?,?,?)",
                (user_id, hid, time.time()))
    return True


async def add_video(user_id, direction, report, score) -> None:
    await _exec("INSERT INTO video_analysis_history(user_id,direction,report,score,created_at) "
                "VALUES(?,?,?,?,?)", (user_id, direction, report, score, time.time()))


async def add_bio(user_id, username, name, bio, profile_url) -> None:
    await _exec("INSERT INTO bio_history(user_id,username,name,bio,profile_url,created_at) "
                "VALUES(?,?,?,?,?,?)", (user_id, username, name, bio, profile_url, time.time()))


async def log_api(source, error) -> None:
    await _exec("INSERT INTO api_logs(source,error,created_at) VALUES(?,?,?)",
                (source, str(error)[:300], time.time()))


async def bump(key) -> None:
    await _exec("INSERT INTO bot_statistics(day,key,count) VALUES(?,?,1) "
                "ON CONFLICT(day,key) DO UPDATE SET count=count+1", (_today(), key))


async def stats() -> dict:
    day_ago = time.time() - 86400
    total = (await _exec("SELECT COUNT(*) c FROM users", one=True))["c"]
    active = (await _exec("SELECT COUNT(*) c FROM users WHERE last_seen>?", (day_ago,), one=True))["c"]
    errors = (await _exec("SELECT COUNT(*) c FROM api_logs WHERE created_at>?", (day_ago,), one=True))["c"]
    rows = await _exec("SELECT key, count FROM bot_statistics WHERE day=?", (_today(),), many=True)
    return {"total": total, "active": active, "errors": errors,
            "today": {r["key"]: r["count"] for r in rows}}
