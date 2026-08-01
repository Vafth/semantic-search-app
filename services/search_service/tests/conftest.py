import pytest
import os
import uuid
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from main import app
from database import get_async_session
from qdrant import get_qdrant_client
from core.config import settings
from repository.vector import build_filename_filter, query_collection


# ── Database ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def engine():
    engine = create_async_engine(
        settings.POSTGRES_URL,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()


# ── Qdrant ──────────────────────────────────────────────────────────────────

@pytest.fixture
def qdrant_client():
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

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


@pytest.fixture
def seed_factory(qdrant_client):
    async def _seed(points):
        collection = list(settings.COLLECTIONS.values())[0]["collection"]
        qdrant_client.upsert(collection_name=collection, points=points)
        return qdrant_client
    return _seed


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


# ── Search params ─────────────────────────────────────────────────────────────

@pytest.fixture
def search_params():
    from schemas.search import SearchParams
    return SearchParams(
        query="Mars",
        model="small_model",
        filenames="test.txt",
        top_k=5,
    )


# ── Point fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def one_point():
    return [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=[0.1] * 384,
            payload={
                "text":        "Mars is the red planet",
                "filename":    "test.txt",
                "document_id": 1,
                "chunk_index": 0,
            }
        )
    ]


@pytest.fixture
def multiple_points():
    return [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=[0.1] * 384,
            payload={
                "text":        "Mars",
                "filename":    "test.txt",
                "document_id": 1,
                "chunk_index": 0,
            }
        ),
        PointStruct(
            id=str(uuid.uuid4()),
            vector=[0.1 if i % 10 == 0 else 0.0 for i in range(384)],
            payload={
                "text":        "Mars is the red planet",
                "filename":    "test.txt",
                "document_id": 1,
                "chunk_index": 0,
            }
        ),
        PointStruct(
            id=str(uuid.uuid4()),
            vector=[0.04] * 384,
            payload={
                "text":        "Mars is the planet",
                "filename":    "test.txt",
                "document_id": 1,
                "chunk_index": 0,
            }
        ),
        PointStruct(
            id=str(uuid.uuid4()),
            vector=[0.04] * 384,
            payload={
                "text":        "Mars is the planet",
                "filename":    "test.txt",
                "document_id": 1,
                "chunk_index": 0,
            }
        ),
        PointStruct(
            id=str(uuid.uuid4()),
            vector=[0.1 if i % 10 == 0 else 0.0 for i in range(384)],
            payload={
                "text":        "Mars is the blue planet",
                "filename":    "test.txt",
                "document_id": 1,
                "chunk_index": 0,
            }
        )
    ]


# ── Search result fixtures ────────────────────────────────────────────────────

@pytest.fixture
async def search_with_single_point(seed_factory, one_point, search_params):
    seeded_qdrant = await seed_factory(one_point)
    f = build_filename_filter([search_params.filenames])
    return await query_collection(
        seeded_qdrant,
        "docs_small_r2",
        [0.1] * 384,
        search_params,
        f,
    )


@pytest.fixture
async def search_with_multiple_points(seed_factory, multiple_points, search_params):
    seeded_qdrant = await seed_factory(multiple_points)
    f = build_filename_filter([search_params.filenames])
    return await query_collection(
        seeded_qdrant,
        "docs_small_r2",
        [0.1] * 384,
        search_params,
        f,
    )


# ── Client with search history (WireMock handles /embed) ─────────────────────

@pytest.fixture
async def client_with_search(client, search_params):
    await client.get(
        "/search",
        params=search_params.model_dump(),
        headers={"x-user-id": "1"}
    )
    return client