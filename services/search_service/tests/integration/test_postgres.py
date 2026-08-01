from repository.postgres import save_search_request, save_search_results, get_requests_by_user, get_results_by_request
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