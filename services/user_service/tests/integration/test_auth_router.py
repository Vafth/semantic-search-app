async def test_register_success(client):
    response = await client.post("/register", json={
        "username": "alice",
        "password": "password123"
    })

    assert response.status_code == 201

async def test_login_returns_token(client, test_user):
    response = await client.post("/login", data={
        "username": "testuser",
        "password": "testpassword123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()