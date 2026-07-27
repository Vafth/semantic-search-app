from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update

from models.user import User
from core.security import get_hash_password

from common.schemas.internal import UserRole

async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return list(result.scalars().all())


async def create_user(
        session:         AsyncSession, 
        username:        str, 
        hashed_password: str, 
        role:            UserRole = UserRole.user
    ) -> User:

    user = User(username=username, hashed_password=hashed_password, role=role)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_fields(session: AsyncSession, user: User, fields: dict) -> User:
    for field, value in fields.items():
        setattr(user, field, value)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def increment_storage_used(db: AsyncSession, user_id: int, delta: int) -> None:
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(storage_used=User.storage_used + delta)
    )
    await db.commit()


async def update_username(db: AsyncSession, user: User, new_username: str) -> User:
    user.username = new_username
    await db.commit()
    await db.refresh(user)
    return user


async def update_password(db: AsyncSession, user: User, new_password: str) -> None:
    user.hashed_password = get_hash_password(new_password)
    await db.commit()