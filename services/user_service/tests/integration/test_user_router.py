from repository.user import update_user_fields, get_user_by_username

async def test_register_success(client):
    response = await client.post("/register", json={
        "username": "alice",
        "password": "password123"
    })

    assert response.status_code == 201


async def test_register_unsuccess(client, test_user):
    response = await client.post("/register", json={
        "username": "testuser",
        "password": "password123"
    })

    assert response.status_code == 409
    assert response.cookies.get("access_token") is None
    assert response.json()["detail"] == "Username already registered"

async def test_login_returns_token(client, test_user):
    response = await client.post("/login", data={
        "username": "testuser",
        "password": "testpassword123"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.cookies.get("access_token") is not None

async def test_login_with_wrong_user(client, test_user):
    response = await client.post("/login", data={
        "username": "nottestuser",
        "password": "testpassword123"
    })
    assert response.status_code == 401
    assert "access_token" not in response.json()
    assert response.json()["detail"] == "Incorrect username or password"

async def test_login_with_wrong_pw(client, test_user):
    response = await client.post("/login", data={
        "username": "testuser",
        "password": "nottestpassword123"
    })
    assert response.status_code == 401
    assert "access_token" not in response.json()

async def test_login_with_inactive_user(db_session, client, test_user):
    user = await get_user_by_username(db_session, test_user["username"])
    assert user
    user = await update_user_fields(db_session, user, {"is_active": False})

    response = await client.post("/login", data={
        "username": "testuser",
        "password": "testpassword123"
    })
    assert response.status_code == 403
    assert response.json()["detail"] == "Account disabled"


async def test_logout(client, test_user):
    response = await client.post("/logout")
    assert response.status_code == 204
    assert response.cookies.get("access_token") is None

async def test_me_successful(client, test_user, auth_token):
    response = await client.get("/me", headers={
        "x-user-id": "1"
    })
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
    assert response.json()["role"] == "user"

async def test_me_user_not_found(client):
    response = await client.get("/me", headers={
        "x-user-id": "99"
    })
    assert response.status_code == 404