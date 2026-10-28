from __future__ import annotations

import asyncio
import json
from typing import Any

from bot.database.session import Database
from bot.utils.time_utils import now_utc


def _now() -> str:
    return now_utc().isoformat()


def _today() -> str:
    return now_utc().strftime("%Y-%m-%d")


class Repository:
    def __init__(self, db: Database):
        self.db = db

    async def _run(self, fn, *a):
        return await asyncio.to_thread(fn, *a)

    # ---------- users ----------
    async def upsert_user(self, user_id: int, username: str | None, first_name: str | None) -> None:
        def f():
            now = _now()
            self.db.execute(
                """INSERT INTO users(user_id, username, first_name, created_at, last_seen)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,
                   first_name=excluded.first_name, last_seen=excluded.last_seen""",
                (user_id, username, first_name, now, now),
            )
        await self._run(f)

    # ---------- hashtag history ----------
    async def add_history(
        self, user_id: int, result_type: str, caption: str = "", hashtags: list[str] | None = None,
        reel_url: str | None = None, video_date: str | None = None, views: int | None = None,
        metric_label: str | None = None, source: str | None = None, direction: str | None = None,
    ) -> int:
        def f():
            return self.db.execute(
                """INSERT INTO hashtag_history(user_id,result_type,reel_url,caption,hashtags,
                   video_date,views,metric_label,source,direction,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (user_id, result_type, reel_url, caption, json.dumps(hashtags or [], ensure_ascii=False),
                 video_date, views, metric_label, source, direction, _now()),
            )
        return await self._run(f)

    @staticmethod
    def _hist_dict(r) -> dict[str, Any]:
        d = dict(r)
        d["hashtags"] = json.loads(d.get("hashtags") or "[]")
        return d

    async def list_history(self, user_id: int, offset: int = 0, limit: int = 10) -> tuple[list[dict], int]:
        def f():
            rows = self.db.query(
                "SELECT * FROM hashtag_history WHERE user_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
                (user_id, limit, offset),
            )
            total = self.db.one("SELECT COUNT(*) c FROM hashtag_history WHERE user_id=?", (user_id,))["c"]
            return [self._hist_dict(r) for r in rows], total
        return await self._run(f)

    async def get_history(self, user_id: int, item_id: int) -> dict | None:
        def f():
            r = self.db.one("SELECT * FROM hashtag_history WHERE id=? AND user_id=?", (item_id, user_id))
            return self._hist_dict(r) if r else None
        return await self._run(f)

    async def delete_history(self, user_id: int, item_id: int) -> bool:
        def f():
            n = self.db.rowcount("DELETE FROM hashtag_history WHERE id=? AND user_id=?", (item_id, user_id))
            self.db.rowcount("DELETE FROM saved_items WHERE history_id=? AND user_id=?", (item_id, user_id))
            return n > 0
        return await self._run(f)

    async def save_item(self, user_id: int, history_id: int | None, note: str = "") -> int:
        return await self._run(
            lambda: self.db.execute(
                "INSERT INTO saved_items(user_id,history_id,note,created_at) VALUES(?,?,?,?)",
                (user_id, history_id, note, _now()),
            )
        )

    # ---------- bio ----------
    async def add_bio(self, user_id: int, username: str, full_name: str, biography: str,
                      profile_url: str, source: str) -> int:
        return await self._run(
            lambda: self.db.execute(
                """INSERT INTO bio_history(user_id,username,full_name,biography,profile_url,source,created_at)
                   VALUES(?,?,?,?,?,?,?)""",
                (user_id, username, full_name, biography, profile_url, source, _now()),
            )
        )

    # ---------- video analysis ----------
    async def add_video_analysis(self, user_id: int, direction: str, score: int, report: str) -> int:
        return await self._run(
            lambda: self.db.execute(
                "INSERT INTO video_analysis_history(user_id,direction,score,report,created_at) VALUES(?,?,?,?,?)",
                (user_id, direction, score, report, _now()),
            )
        )

    # ---------- logs & stats ----------
    async def log_api(self, source: str, ok: bool, message: str = "") -> None:
        await self._run(
            lambda: self.db.execute(
                "INSERT INTO api_logs(source,ok,message,created_at) VALUES(?,?,?,?)",
                (source, 1 if ok else 0, message[:500], _now()),
            )
        )

    async def bump(self, metric: str, n: int = 1) -> None:
        def f():
            self.db.execute(
                """INSERT INTO bot_statistics(day,metric,value) VALUES(?,?,?)
                   ON CONFLICT(day,metric) DO UPDATE SET value=value+excluded.value""",
                (_today(), metric, n),
            )
        await self._run(f)

    async def stats(self) -> dict[str, Any]:
        def f():
            d = self.db
            today = _today()
            since = now_utc().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            week = (now_utc().timestamp() - 7 * 86400)
            from datetime import datetime, timezone
            week_iso = datetime.fromtimestamp(week, timezone.utc).isoformat()

            def metric(name: str, all_time: bool = False) -> int:
                if all_time:
                    r = d.one("SELECT COALESCE(SUM(value),0) v FROM bot_statistics WHERE metric=?", (name,))
                else:
                    r = d.one("SELECT COALESCE(SUM(value),0) v FROM bot_statistics WHERE metric=? AND day=?",
                              (name, today))
                return r["v"]

            sources = d.query(
                """SELECT source, SUM(ok) ok, COUNT(*) total, MAX(created_at) last
                   FROM api_logs WHERE created_at>=? GROUP BY source""", (week_iso,))
            return {
                "users_total": d.one("SELECT COUNT(*) c FROM users")["c"],
                "users_active_7d": d.one("SELECT COUNT(*) c FROM users WHERE last_seen>=?", (week_iso,))["c"],
                "users_today": d.one("SELECT COUNT(*) c FROM users WHERE last_seen>=?", (since,))["c"],
                "actions_today": metric("action"),
                "top_total": metric("top", True),
                "gen_total": metric("generator", True),
                "video_total": metric("video", True),
                "api_errors_7d": d.one("SELECT COUNT(*) c FROM api_logs WHERE ok=0 AND created_at>=?",
                                       (week_iso,))["c"],
                "sources": [dict(r) for r in sources],
            }
        return await self._run(f)
