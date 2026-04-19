from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from core.config import settings
from core.security import UserDep, authenticate_user, create_access_token, get_hash_password
from database import AsyncSessionDep
from models.user import User, UserRole
from schemas.user import Token, UserCreate, UserRead, UserUpdate
from repository.user import (
    get_user_by_username,
    get_user_by_id,
    get_all_users,
    create_user,
    update_user_fields,
)

router = APIRouter(tags=["user"])


# ── Public ────────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, session: AsyncSessionDep):
    existing = await get_user_by_username(session, body.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")

    return await create_user(
        session          = session,
        username         = body.username,
        hashed_password  = get_hash_password(body.password),
    )


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form:     Annotated[OAuth2PasswordRequestForm, Depends()],
    session:  AsyncSessionDep,
):
    user = await authenticate_user(session, form.username, form.password)
    if not user:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Incorrect username or password",
            headers     = {"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    token = create_access_token(
        data          = {"sub": str(user.id), "role": user.role},
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    response.set_cookie(
        key      = "access_token",
        value    = f"Bearer {token}",
        httponly = True,
        samesite = "lax",
        secure   = False,
        max_age  = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return Token(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie("access_token")


# ── Authenticated user ────────────────────────────────────────────────────────

@router.get("/me", response_model=UserRead)
async def me(current_user: UserDep):
    return current_user


# ── Admin ─────────────────────────────────────────────────────────────────────

def require_admin(current_user: UserDep) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    return current_user

AdminDep = Annotated[User, Depends(require_admin)]


@router.get("/users", response_model=list[UserRead])
async def list_users(_: AdminDep, session: AsyncSessionDep):
    return await get_all_users(session)


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(user_id: int, body: UserUpdate, _: AdminDep, session: AsyncSessionDep):
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await update_user_fields(session, user, body.model_dump(exclude_unset=True))