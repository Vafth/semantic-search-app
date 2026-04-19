from typing import Annotated
from datetime import datetime

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel
import jwt
from jwt.exceptions import InvalidTokenError

from core.config import settings


# ── Token model ───────────────────────────────────────────────────────────────

class TokenClaims(BaseModel):
    sub:  str       # user_id as string
    role: str
    exp:  datetime


# ── Token extraction ──────────────────────────────────────────────────────────

class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str | None:
        header_auth = request.headers.get("Authorization")
        if header_auth:
            scheme, params = get_authorization_scheme_param(header_auth)
            if scheme.lower() == "bearer":
                return params

        cookie = request.cookies.get("access_token")
        if not cookie:
            if self.auto_error:
                raise HTTPException(
                    status_code = status.HTTP_401_UNAUTHORIZED,
                    detail      = "Not authenticated",
                    headers     = {"WWW-Authenticate": "Bearer"},
                )
            return None

        return cookie.removeprefix("Bearer ").strip()


_oauth2_scheme = OAuth2PasswordBearerWithCookie(
    tokenUrl   = "/auth/login",
    auto_error = True,
)


# ── Dependencies ──────────────────────────────────────────────────────────────

async def get_verified_claims(
    token: Annotated[str, Depends(_oauth2_scheme)],
) -> TokenClaims:
    """
    Validates JWT signature and expiry only.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return TokenClaims(**payload)
    except (InvalidTokenError, Exception):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Could not validate credentials",
            headers     = {"WWW-Authenticate": "Bearer"},
        )


ClaimsDep = Annotated[TokenClaims, Depends(get_verified_claims)]


def build_internal_headers(claims: TokenClaims) -> dict[str, str]:

    return {
        "X-User-Id":   claims.sub,
        "X-User-Role": claims.role,
    }