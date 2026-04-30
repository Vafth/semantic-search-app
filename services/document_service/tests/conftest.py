import pytest

from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

from sqlmodel import SQLModel
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import qdrant as qdrant_module 
from qdrant_client.models import PointStruct

from main import app
from core.config import settings
from database import get_async_session
from qdrant import get_qdrant_client
from schemas.document import DocumentCreate
from repository.vector import store_chunks
from repository.postgres import create_document


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
    client = QdrantClient(":memory:")
    
    # create test collections
    for model_name, cfg in settings.COLLECTIONS.items():
        client.create_collection(
            collection_name = cfg["collection"],
            vectors_config  = VectorParams(
                size     = cfg["vector_size"],
                distance = Distance.COSINE,
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

    # inject into the global
    qdrant_module._client = qdrant_client

    async with AsyncClient(
        transport = ASGITransport(app=app),
        base_url  = "http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    qdrant_module._client = None

@pytest.fixture
async def client_with_file(client):
    
    with patch("routers.document.index_document"):
        response = await client.post(
            "/upload",
            files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
            headers={"x-user-id": "1"}
        )

    return client

# ── Seed data ─────────────────────────────────────────────────────────────────

@pytest.fixture
def new_document():
    return DocumentCreate(
        filename     = "test.txt",
        file_size    = 20,
        content_type = "text/html",
    )

@pytest.fixture
async def session_with_document(db_session, new_document):
    db_document = await create_document(db_session, new_document, 1)
    
    assert db_document.status == "processing"
    
    return db_session


@pytest.fixture
async def seeded_qdrant_client(qdrant_client):
    await store_chunks(
        qdrant     = qdrant_client,
        chunks     = ["Mars is a red planet"],
        vectors    = [[0.1] * 384],
        doc_id     = 1,
        filename   = "test.txt",
        model_name = list(settings.COLLECTIONS.keys())[0],
        cfg        = settings.COLLECTIONS["small_model"],
    )
    return qdrant_client

# ── Mocks ────────────────────────────────────────────────────────────────────
@pytest.fixture
def mock_index_document():
    with patch("routers.document.index_document") as m:
        m.return_value = None
        yield m

@pytest.fixture
def mock_get_embeddings():
    with patch("core.processor.get_embeddings") as m:
        m.return_value = None
        yield m