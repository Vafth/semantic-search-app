import pytest
from unittest.mock import MagicMock, patch

from qdrant_client.http.exceptions import UnexpectedResponse

from repository.vector import store_chunks, get_chunks_by_document, delete_points_by_document
from core.config import settings


async def test_qdrant_interaction(qdrant_client):
    await store_chunks(
        qdrant     = qdrant_client,
        chunks     = ["Mars is a red planet"],
        vectors    = [[0.1] * 384],
        doc_id     = 1,
        filename   = "test.txt",
        model_name = list(settings.COLLECTIONS.keys())[0],
        cfg        = list(settings.COLLECTIONS.values())[0],
    )

    chunks = await get_chunks_by_document(qdrant_client, 1)
    assert chunks == "Mars is a red planet"

    await delete_points_by_document(qdrant_client, 1)
    chunks = await get_chunks_by_document(qdrant_client, 1)

    assert chunks == ""


# ── get_chunks_by_document ────────────────────────────────────────────────────

async def test_get_chunks_returns_empty_when_no_results(qdrant_client):
    # empty collection → scroll returns [] → returns ""
    result = await get_chunks_by_document(qdrant_client, document_id=999)
    assert result == ""


async def test_get_chunks_returns_text(seeded_qdrant_client):
    result = await get_chunks_by_document(seeded_qdrant_client, document_id=1)
    assert isinstance(result, str)
    assert len(result) > 0


# ── delete_points_by_document ─────────────────────────────────────────────────

async def test_delete_points_returns_empty_on_success(qdrant_client):
    failed = await delete_points_by_document(qdrant_client, doc_id=1)
    assert failed == []


async def test_delete_points_returns_failed_collections_on_error(qdrant_client):
    with patch.object(qdrant_client, "delete", side_effect=Exception("connection lost")):
        failed = await delete_points_by_document(qdrant_client, doc_id=1)

    assert len(failed) == len(settings.COLLECTIONS)
    for _, cfg in settings.COLLECTIONS.items():
        assert cfg["collection"] in failed