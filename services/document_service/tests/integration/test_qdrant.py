import pytest
from qdrant_client import QdrantClient
from qdrant import init_qdrant, get_qdrant_client
from core.config import settings


def test_init_qdrant_creates_collections():
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    for _, cfg in settings.COLLECTIONS.items():
        client.delete_collection(cfg["collection"])

    init_qdrant()

    existing = [c.name for c in client.get_collections().collections]
    for _, cfg in settings.COLLECTIONS.items():
        assert cfg["collection"] in existing
    client.close()


def test_init_qdrant_skips_existing_collections():
    init_qdrant()

    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    existing = [c.name for c in client.get_collections().collections]
    for _, cfg in settings.COLLECTIONS.items():
        assert cfg["collection"] in existing
    client.close()


def test_get_qdrant_client_returns_client():
    init_qdrant()
    client = get_qdrant_client()
    assert client is not None
    assert isinstance(client, QdrantClient)