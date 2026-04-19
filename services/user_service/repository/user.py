from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.user import User


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return list(result.scalars().all())


async def create_user(session: AsyncSession, username: str, hashed_password: str) -> User:
    user = User(username=username, hashed_password=hashed_password)
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