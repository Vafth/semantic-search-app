from repository.user import *

async def test_create_user(db_session):
    db_user = await create_user(db_session, username = "new_user", hashed_password="1234567890")

    assert db_user.id == 1
    assert db_user.role == "user"

async def test_get_user_by_username(db_session, test_user):
    new_user = await get_user_by_username(db_session, test_user["username"])

    assert new_user

async def test_get_user_by_id(db_session, test_user):
    new_user = await get_user_by_username(db_session, test_user["username"])
    assert new_user

    searched_user = await get_user_by_id(db_session, new_user.id)
    assert searched_user == new_user

async def test_get_all_users(db_session, test_user):
    all_users = await get_all_users(db_session)

    assert len(all_users) == 1
    assert all_users[0].username == "testuser"

async def test_update_user(db_session, test_user):
    user = await get_user_by_username(db_session, username = test_user["username"])
    new_admin = await update_user_fields(db_session, user, {"role": "admin"})

    assert new_admin.id == 1
    assert new_admin.role == "admin"
    assert new_admin.updated_at is not None