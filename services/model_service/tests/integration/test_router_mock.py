from unittest.mock import patch

# ── embed ─────────────────────────────────────────────────────────────────────

async def test_embed_unloaded_model(client, embed_request_unloaded_model):
    
    response = await client.post(
        "/embed",
        json = embed_request_unloaded_model.model_dump()
    )
    
    assert response.status_code == 500
    assert response.json()["detail"] == f"Model {embed_request_unloaded_model.model} is not loaded."

async def test_embed(client, embed_request):
    
    response = await client.post(
        "/embed",
        json = embed_request.model_dump()
    )

    assert response.status_code == 200
    assert len(response.json()["vectors"]) == 1
    assert len(response.json()["vectors"][0]) == 384