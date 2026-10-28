from datetime import datetime, timedelta, timezone

from bot.utils.time_utils import cutoff_7d, parse_ts, within_7_days

NOW = datetime(2026, 10, 27, 20, 0, tzinfo=timezone.utc)


def test_cutoff_is_exactly_7x24h():
    assert cutoff_7d(NOW) == datetime(2026, 10, 20, 20, 0, tzinfo=timezone.utc)


def test_old_video_excluded():
    assert not within_7_days(NOW - timedelta(days=3650), NOW)
    assert not within_7_days(NOW - timedelta(days=7, minutes=1), NOW)


def test_recent_video_included():
    assert within_7_days(NOW - timedelta(days=6, hours=23), NOW)
    assert not within_7_days(None, NOW)


def test_parse_ts_formats():
    assert parse_ts("2026-10-25T10:00:00+0000") == datetime(2026, 10, 25, 10, tzinfo=timezone.utc)
    assert parse_ts("2026-10-25T10:00:00Z").hour == 10
    assert parse_ts("xx") is None
