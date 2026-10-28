import os
from dotenv import load_dotenv

load_dotenv()


def _ids(raw: str) -> tuple[int, ...]:
    return tuple(int(x) for x in raw.split(",") if x.strip().isdigit())


class Config:
    bot_token = os.getenv("BOT_TOKEN", "")
    admin_ids = _ids(os.getenv("ADMIN_IDS", ""))
    channel = os.getenv("CHANNEL_USERNAME", "@o11abu")
    webapp_url = os.getenv("WEBAPP_URL", "").rstrip("/")
    port = int(os.getenv("PORT", "8080"))
    db_path = os.getenv("DB_PATH", "hashtag_ai.db")
    ig_token = os.getenv("IG_ACCESS_TOKEN", "")
    ig_user_id = os.getenv("IG_USER_ID", "")
    oembed_token = os.getenv("IG_OEMBED_TOKEN", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


cfg = Config()
