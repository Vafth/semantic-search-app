import pytest
from httpx import HTTPError

from core.config import settings


# ── search ────────────────────────────────────────────────────────────────────

async def test_search_wrong_modelname(client):
    response = await client.get(
        "/search",
        params={"query": "Mars", "model": "123", "top_k": 5, "score": 0.4, 
                "dif": 0.0, "filenames": "test.txt", "refine": False, 
                "deep": True, "deep_min": 0.0},
        headers={"x-user-id": "1"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == f"Unknown model '123'. Choose from: {list(settings.COLLECTIONS.keys())}"


async def test_search_model_service_fail(client, search_params):
    response = await client.get(
        "/search",
        params  = search_params.model_dump(),
        headers = {"x-user-id": "1"}
    )
    
    assert response.status_code == 502
    assert response.json()["detail"] == "Model service error: Model service connection failed"


async def test_search(client, search_params):
    response = await client.get(
        "/search",
        params  = search_params.model_dump(),
        headers = {"x-user-id": "1"}
    )
    
    
    assert response.status_code == 200
    assert response.json()["query"] == search_params.query


# ── history ───────────────────────────────────────────────────────────────────

async def test_empty_history(client):
    response = await client.get(
        "/history",
        headers = {"x-user-id": "1"}
    )

    assert response.status_code == 200
    assert response.json() == []

async def test_history(client_with_search):
    response = await client_with_search.get(
        "/history",
        headers = {"x-user-id": "1"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["query"] == "Mars"
