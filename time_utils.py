from __future__ import annotations

from datetime import datetime, timedelta, timezone

UTC = timezone.utc


def now_utc() -> datetime:
    return datetime.now(UTC)


def cutoff_7d(now: datetime | None = None) -> datetime:
    """Aniq oxirgi 7 x 24 soat chegarasi."""
    return (now or now_utc()) - timedelta(days=7)


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    v = value.strip().replace("Z", "+00:00")
    if len(v) >= 5 and v[-5] in "+-" and v[-3] != ":":  # +0000 -> +00:00
        v = v[:-2] + ":" + v[-2:]
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def within_7_days(dt: datetime | None, now: datetime | None = None) -> bool:
    if dt is None:
        return False
    now = now or now_utc()
    return cutoff_7d(now) <= dt <= now + timedelta(minutes=5)


def fmt_dt(dt: datetime | None) -> str:
    return dt.astimezone(UTC).strftime("%d.%m.%Y %H:%M UTC") if dt else "—"
