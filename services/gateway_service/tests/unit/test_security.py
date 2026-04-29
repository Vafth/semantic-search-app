import pytest

from fastapi import HTTPException

from core.security import OAuth2PasswordBearerWithCookie


oauth2 = OAuth2PasswordBearerWithCookie(tokenUrl="/auth/login", auto_error=True)


async def test_extracts_token_from_header(request_with_token_in_headers):
    token = await oauth2(request_with_token_in_headers)
    assert token == "mytoken123"

async def test_extracts_token_from_cookie(request_with_token_in_cookies):
    token = await oauth2(request_with_token_in_cookies)
    assert token == "mytoken123"


async def test_raises_401_when_no_token(request_without_token):
    with pytest.raises(HTTPException) as exc:
        await oauth2(request_without_token)
    assert exc.value.status_code == 401

async def test_header_takes_priority_over_cookie(request_with_token_in_both):
    token = await oauth2(request_with_token_in_both)
    assert token == "headertoken"