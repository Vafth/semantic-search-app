from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
import jwt
import bcrypt

from core.config import settings
from database import AsyncSessionDep
from models.user import User
from repository.user import get_user_by_id, get_user_by_username


async def authenticate_user(session: AsyncSessionDep, username: str, password: str) -> User | None:
    user = await get_user_by_username(session, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# ── Password ──────────────────────────────────────────────────────────────────

def get_hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        plain.encode("utf-8"),
        hashed.encode("utf-8")
    )

# ── Token creation ────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire    = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ── Request identity ──────────────────────────────────────────────────────────

async def get_current_user(
    session:     AsyncSessionDep,
    x_user_id:   Annotated[int, Header()],
) -> User:
    user = await get_user_by_id(session, x_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


UserDep = Annotated[User, Depends(get_current_user)]