from unittest.mock import patch, AsyncMock
import httpx

from repository.postgres import save_search_request, save_search_results, get_requests_by_user, get_results_by_request, delete_request_by_user
from repository.vector import build_filename_filter, query_collection

async def test_save_search_request(db_session, search_params):
    search_request_id = await save_search_request(db_session, 1, search_params)
    
    assert isinstance(search_request_id, int)
    assert search_request_id > 0

    db_search_request = await get_requests_by_user(db_session, 1)
    assert len(db_search_request) == 1
    assert db_search_request[0].id == search_request_id


# Helper
async def search_single_point(seed_factory, one_point, search_params):
    seeded_qdrant = await seed_factory(one_point)
    f = build_filename_filter([search_params.filenames])
    return await query_collection(
        seeded_qdrant, "docs_small_r2", [0.1] * 384, search_params, f
    )


async def test_search(client, seed_factory, one_point, search_params):
    results = await search_single_point(seed_factory, one_point, search_params)

    assert len(results) == 1
    assert results[0].text == "Mars is the red planet"
    assert results[0].filename == "test.txt"
    assert results[0].chunk_index == 0


async def test_save_search_results(db_session, seed_factory, one_point, search_params):
    # 1. Save the request first
    search_request_id = await save_search_request(db_session, 1, search_params)
    assert isinstance(search_request_id, int)
    
    # 2. Perform the actual Qdrant search via the helper
    search_results = await search_single_point(seed_factory, one_point, search_params)
    
    # 3. Persist results to Postgres
    await save_search_results(db_session, search_request_id, search_results)
    
    # 4. Verify
    db_search_results = await get_results_by_request(db_session, search_request_id)
    assert len(db_search_results) == 1

# ── embed service failure ─────────────────────────────────────────────────────

async def test_search_embed_error_returns_502(client, search_params):
    with patch("routers.search.embed_query", new_callable=AsyncMock) as mock_embed:
        mock_embed.side_effect = httpx.HTTPError("connection refused")
        response = await client.get(
            "/search",
            params  = search_params.model_dump(),
            headers = {"x-user-id": "1"},
        )
    assert response.status_code == 502
    assert "Model service error" in response.json()["detail"]


# ── deep search branch ────────────────────────────────────────────────────────

async def test_search_with_deep_enabled(client, search_params):
    params = search_params.model_dump()
    params["deep"] = True
    response = await client.get(
        "/search",
        params  = params,
        headers = {"x-user-id": "1"},
    )
    assert response.status_code == 200
    assert "results" in response.json()


# ── refine branch ─────────────────────────────────────────────────────────────

async def test_search_with_refine_enabled(client, search_params):
    params = search_params.model_dump()
    params["refine"] = True
    response = await client.get(
        "/search",
        params  = params,
        headers = {"x-user-id": "1"},
    )
    assert response.status_code == 200
    assert "results" in response.json()


# ── save + return on success ──────────────────────────────────────────────────

async def test_search_saves_request_and_returns_response(client, search_params):
    response = await client.get(
        "/search",
        params  = search_params.model_dump(),
        headers = {"x-user-id": "1"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["query"]      == search_params.query
    assert body["model"]      == search_params.model
    assert body["collection"] is not None
    assert isinstance(body["results"], list)


# ── delete_request_by_user ────────────────────────────────────────────────────

async def test_delete_request_by_user_exists(db_session, search_params):
    request_id = await save_search_request(db_session, 1, search_params)

    await delete_request_by_user(db_session, request_id, user_id=1)

    remaining = await get_requests_by_user(db_session, 1)
    assert len(remaining) == 0


async def test_delete_request_by_user_wrong_user(db_session, search_params):
    request_id = await save_search_request(db_session, 1, search_params)

    await delete_request_by_user(db_session, request_id, user_id=2)

    remaining = await get_requests_by_user(db_session, 1)
    assert len(remaining) == 1


async def test_delete_request_by_user_not_found(db_session):
    # non-existent id — should silently do nothing, not raise
    await delete_request_by_user(db_session, request_id=999, user_id=1)


# ── delete history endpoint ───────────────────────────────────────────────────

async def test_delete_search_request(client_with_search):
    # get the saved request id first
    history = await client_with_search.get(
        "/history",
        headers={"x-user-id": "1"},
    )
    request_id = history.json()[0]["id"]

    response = await client_with_search.delete(
        f"/history/{request_id}",
        headers={"x-user-id": "1"},
    )
    assert response.status_code == 204

    # verify it's gone
    history_after = await client_with_search.get(
        "/history",
        headers={"x-user-id": "1"},
    )
    assert len(history_after.json()) == 0


async def test_delete_search_request_wrong_user(client_with_search):
    # user 2 cannot delete user 1's request
    history = await client_with_search.get(
        "/history",
        headers={"x-user-id": "1"},
    )
    request_id = history.json()[0]["id"]

    response = await client_with_search.delete(
        f"/history/{request_id}",
        headers={"x-user-id": "2"},
    )
    assert response.status_code == 204  # silent — no 403, just does nothing

    # user 1's request is still there
    history_after = await client_with_search.get(
        "/history",
        headers={"x-user-id": "1"},
    )
    assert len(history_after.json()) == 1


async def test_delete_search_request_not_found(client):
    response = await client.delete(
        "/history/999",
        headers={"x-user-id": "1"},
    )
    assert response.status_code == 204  # silent no-op