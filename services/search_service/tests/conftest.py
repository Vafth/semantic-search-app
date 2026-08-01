import pytest
import os

from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

from main import app
from database import get_async_session
from qdrant import get_qdrant_client
from core.config import settings


# ── Database ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def engine():
    engine = create_async_engine(
        settings.POSTGRES_URL, 
        echo=False,
        poolclass = NullPool
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(engine):
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()


@pytest.fixture
def qdrant_client():
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    
    # Recreate collections
    for model_name, cfg in settings.COLLECTIONS.items():
        client.recreate_collection(
            collection_name=cfg["collection"],
            vectors_config=VectorParams(
                size=cfg["vector_size"],
                distance=Distance.COSINE,
            ),
        )
    yield client
    client.close()


# ── App client ────────────────────────────────────────────────────────────────

@pytest.fixture
async def client(db_session, qdrant_client):
    # override both dependencies
    async def override_get_session():
        yield db_session

    def override_get_qdrant():
        return qdrant_client

    app.dependency_overrides[get_async_session] = override_get_session
    app.dependency_overrides[get_qdrant_client] = override_get_qdrant

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()