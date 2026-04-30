import pytest

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

async def test_qdrant_interaction_wrong_collection(qdrant_client):
    with pytest.raises(ValueError, match="Collection 123 not found"):
        await store_chunks(
            qdrant     = qdrant_client,
            chunks     = ["Mars is a red planet"],
            vectors    = [[0.1] * 384],
            doc_id     = 1,
            filename   = "test.txt",
            model_name = "123",
            cfg        = {
                "collection":  "123",
                "vector_size": 384,
            },
        )

    chunks = await get_chunks_by_document(qdrant_client, 1)
    assert chunks == ""