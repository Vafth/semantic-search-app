from core.security import build_internal_headers
from core.security import OAuth2PasswordBearerWithCookie

oauth2 = OAuth2PasswordBearerWithCookie(tokenUrl="/auth/login", auto_error=True)


def test_build_internal_headers(claim_admin):
    headers = build_internal_headers(claim_admin)
    assert headers["X-User-Id"] == "42"
    assert headers["X-User-Role"] == "admin"
