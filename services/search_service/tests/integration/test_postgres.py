from repository.postgres import save_search_request, save_search_results, get_requests_by_user, get_results_by_request

async def test_save_search_request(db_session, search_params):
    search_request_id = await save_search_request(db_session, 1, search_params)
    
    assert search_request_id == 1

    db_search_reqeust = await get_requests_by_user(db_session, 1)
    assert len(db_search_reqeust) == 1

async def test_save_search_results(db_session, search_with_single_point, search_params):
    search_request_id = await save_search_request(db_session, 1, search_params)
    
    await save_search_results(db_session, search_request_id, search_with_single_point)
    
    db_search_results = await get_results_by_request(db_session, search_request_id)
    assert len(db_search_results) == 1