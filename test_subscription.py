import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
from aiogram.enums import ChatMemberStatus

from bot.config import settings
from bot.services import subscription_service as ss
from bot.webapi import validate_init_data


class FakeBot:
    def __init__(self, status=None, exc=None):
        self.status, self.exc = status, exc

    async def get_chat_member(self, chat, uid):
        if self.exc:
            raise self.exc
        return SimpleNamespace(status=self.status)


async def test_member_ok_and_left_blocked():
    ss.clear_cache()
    assert await ss.is_subscribed(FakeBot(ChatMemberStatus.MEMBER), 7)
    ss.clear_cache()
    assert not await ss.is_subscribed(FakeBot(ChatMemberStatus.LEFT), 7)


async def test_api_error_raises():
    ss.clear_cache()
    with pytest.raises(ss.SubscriptionError):
        await ss.is_subscribed(FakeBot(exc=RuntimeError("boom")), 8)


async def test_admin_bypasses():
    assert await ss.is_subscribed(FakeBot(ChatMemberStatus.LEFT), 111)


def _init(token, user, age=0):
    data = {"auth_date": str(int(time.time()) - age), "user": json.dumps(user)}
    check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    data["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(data)


def test_init_data_validation():
    u = {"id": 42, "first_name": "A"}
    assert validate_init_data(_init(settings.bot_token, u), settings.bot_token)["id"] == 42
    assert validate_init_data(_init("999:wrong", u), settings.bot_token) is None
    assert validate_init_data(_init(settings.bot_token, u, age=999999), settings.bot_token) is None
    assert validate_init_data("", settings.bot_token) is None
