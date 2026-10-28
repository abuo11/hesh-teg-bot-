from __future__ import annotations

from bot.services.instagram_api import InstagramAPI, Profile, SourceError
from bot.utils.validators import parse_username


async def get_bio(raw: str, api: InstagramAPI) -> Profile:
    username = parse_username(raw)
    if not username:
        raise SourceError("Username noto‘g‘ri. Namuna: @username yoki https://instagram.com/username")
    profile = await api.fetch_profile(username)
    if not (profile.biography or profile.name):
        raise SourceError("Profilda bio ma’lumoti topilmadi.")
    return profile
