from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _ids(value: str) -> list[int]:
    out = []
    for part in value.replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            out.append(int(part))
    return out


@dataclass(frozen=True)
class Settings:
    bot_token: str = ""
    admin_ids: list[int] = field(default_factory=list)
    required_channel: str = "@o11abu"
    required_channel_url: str = "https://t.me/o11abu"
    signature: str = "Тг канал : @o11abu"
    webapp_url: str = ""
    web_host: str = "0.0.0.0"
    web_port: int = 8080
    ig_oembed_token: str = ""
    ig_user_id: str = ""
    ig_access_token: str = ""
    gemini_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    db_path: str = "data/hashtag_ai.db"
    max_video_mb: int = 20
    rate_limit: int = 20

    @property
    def db_file(self) -> Path:
        p = Path(self.db_path)
        return p if p.is_absolute() else BASE_DIR / p

    @property
    def webapp_dir(self) -> Path:
        return BASE_DIR / "webapp"


def load_settings() -> Settings:
    g = os.getenv
    return Settings(
        bot_token=g("BOT_TOKEN", ""),
        admin_ids=_ids(g("ADMIN_IDS", "")),
        required_channel=g("REQUIRED_CHANNEL", "@o11abu"),
        required_channel_url=g("REQUIRED_CHANNEL_URL", "https://t.me/o11abu"),
        signature=g("CHANNEL_SIGNATURE", "Тг канал : @o11abu"),
        webapp_url=g("WEBAPP_URL", "").rstrip("/"),
        web_host=g("WEB_HOST", "0.0.0.0"),
        web_port=int(g("PORT", g("WEB_PORT", "8080"))),
        ig_oembed_token=g("INSTAGRAM_OEMBED_TOKEN", ""),
        ig_user_id=g("INSTAGRAM_USER_ID", ""),
        ig_access_token=g("INSTAGRAM_ACCESS_TOKEN", ""),
        gemini_key=g("GEMINI_API_KEY", ""),
        gemini_model=g("GEMINI_MODEL", "gemini-2.5-flash"),
        db_path=g("DATABASE_PATH", "data/hashtag_ai.db"),
        max_video_mb=int(g("MAX_VIDEO_MB", "20")),
        rate_limit=int(g("RATE_LIMIT_PER_MIN", "20")),
    )


settings = load_settings()
