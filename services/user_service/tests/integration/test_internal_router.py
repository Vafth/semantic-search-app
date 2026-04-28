from repository.user import update_user_fields, get_user_by_username

async def test_user_verify(client, test_user):
    response = await client.get("/internal/verify/1")

    assert response.status_code == 200
    assert response.json()["ok"] == True


async def test_user_verify_not_found(client, test_user):
    
    response = await client.get("/internal/verify/99")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


async def test_user_verify_inactive(client, db_session, test_user):
    user = await get_user_by_username(db_session, test_user["username"])
    assert user
    
    user = await update_user_fields(db_session, user, {"is_active": False})
    
    response = await client.get(f"/internal/verify/{user.id}")
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Account disabled"