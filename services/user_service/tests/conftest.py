import pytest

from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from main import app
from core.config import settings
from database import get_async_session


# ── Database ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def engine():
    engine = create_async_engine(settings.POSTGRES_URL, echo=False)
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

# ── App client ────────────────────────────────────────────────────────────────

@pytest.fixture
async def client(db_session):
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

# ── Seed data ─────────────────────────────────────────────────────────────────

@pytest.fixture
async def test_user(client):
    response = await client.post("/register", json={
        "username": "testuser",
        "password": "testpassword123"
    })
    assert response.status_code == 201
    return response.json()

@pytest.fixture
async def auth_token(client, test_user):
    response = await client.post("/login", data={
        "username": "testuser",
        "password": "testpassword123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]