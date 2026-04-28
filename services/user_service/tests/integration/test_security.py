from core.security import authenticate_user, get_current_user

async def test_authenticate_user(db_session, test_user):
    db_user = await authenticate_user(db_session, "testuser", "testpassword123")
    
    assert db_user

async def test_not_authenticate_user(db_session, test_user):
    db_user = await authenticate_user(db_session, "testuser1", "testpassword123")
    
    assert db_user is None

async def test_get_cur_user(db_session, test_user):
    db_user = await get_current_user(db_session, 1)
    
    assert db_user