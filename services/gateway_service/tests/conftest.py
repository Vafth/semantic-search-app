from datetime import datetime, timezone

import pytest
from unittest.mock import MagicMock

from core.security import TokenClaims


async def make_claims(**kwargs):
    defaults = {
        "sub": "123",
        "role": "user",
        "exp": datetime(2099, 1, 1, tzinfo=timezone.utc)
    }
    return TokenClaims(**{**defaults, **kwargs})


def make_request(headers=None, cookies=None):
    request = MagicMock()
    request.headers.get = lambda k, d=None: (headers or {}).get(k, d)
    request.cookies.get = lambda k, d=None: (cookies or {}).get(k, d)
    return request


@pytest.fixture
async def claim_user():
    return await make_claims()

@pytest.fixture
async def claim_admin():
    return await make_claims(sub="42", role="admin")


@pytest.fixture
async def request_with_token_in_headers():
    return make_request(headers={"Authorization": "Bearer mytoken123"})

@pytest.fixture
async def request_with_token_in_cookies():
    return make_request(cookies={"access_token": "Bearer mytoken123"})

@pytest.fixture
async def request_with_token_in_both():
    return make_request(
        headers={"Authorization": "Bearer headertoken"},
        cookies={"access_token": "Bearer cookietoken"}
    )

@pytest.fixture
async def request_without_token():
    return make_request()