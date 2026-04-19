from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from collections.abc import AsyncGenerator
from sqlmodel import SQLModel

from core.config import settings

async_engine = create_async_engine(
    settings.POSTGRES_URL,
    echo=True,                    # set True only in dev
    pool_pre_ping=True,           # good for Docker
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]

async def create_db_and_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)