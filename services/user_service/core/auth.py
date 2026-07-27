from typing import Annotated
from fastapi import Header, HTTPException, status, Depends

from db.deps import AsyncSessionDep
from repository.user import get_user_by_id, get_user_by_username
from core.security import verify_password
from models.user import User

async def authenticate_user(session: AsyncSessionDep, username: str, password: str) -> User | None:
    user = await get_user_by_username(session, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(
    session:   AsyncSessionDep,
    x_user_id: Annotated[int, Header()],
) -> User:
    user = await get_user_by_id(session, x_user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Inactive user")
    return user

UserDep = Annotated[User, Depends(get_current_user)]