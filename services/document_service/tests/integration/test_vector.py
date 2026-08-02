import pytest
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