import pytest
from unittest.mock import MagicMock
from core.processor import manager

from httpx import AsyncClient, ASGITransport

from main import app
from routers.embed import EmbedRequest

# ── App client ────────────────────────────────────────────────────────────────

@pytest.fixture
async def client():

    async with AsyncClient(
        transport = ASGITransport(app=app),
        base_url  = "http://test",
    ) as ac:
        yield ac

@pytest.fixture(autouse=True)
def mock_models():
    mock = MagicMock()
    mock.encode.return_value.tolist.return_value = [[0.1] * 384]
    manager.models = {
        "small_model":        mock,
        "normal_model":       mock,
    }
    yield manager
    
    manager.models = {}

@pytest.fixture()
def embed_request():
    return EmbedRequest(
        model = "small_model",
        texts = ["123", "123"],
        batch_size = 32
    )

@pytest.fixture()
def embed_request_unloaded_model():
    return EmbedRequest(
        model = "multilingual_model",
        texts = ["123", "123"],
        batch_size = 32
    )