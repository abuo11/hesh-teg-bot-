"""SQLite sxemasi. Jadvallar bot ishga tushganda avtomatik yaratiladi."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    created_at  TEXT NOT NULL,
    last_seen   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hashtag_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    result_type  TEXT NOT NULL,          -- reel_caption | ai_generated | top3
    reel_url     TEXT,
    caption      TEXT,
    hashtags     TEXT NOT NULL DEFAULT '[]',   -- JSON ro'yxat
    video_date   TEXT,
    views        INTEGER,
    metric_label TEXT,
    source       TEXT,
    direction    TEXT,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_hh_user ON hashtag_history(user_id, id DESC);

CREATE TABLE IF NOT EXISTS bio_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    username     TEXT NOT NULL,
    full_name    TEXT,
    biography    TEXT,
    profile_url  TEXT,
    source       TEXT,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_bio_user ON bio_history(user_id, id DESC);

CREATE TABLE IF NOT EXISTS video_analysis_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    direction   TEXT,
    score       INTEGER,
    report      TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS saved_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    history_id  INTEGER,
    note        TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS api_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT NOT NULL,
    ok          INTEGER NOT NULL,
    message     TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bot_statistics (
    day     TEXT NOT NULL,
    metric  TEXT NOT NULL,
    value   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (day, metric)
);
"""
