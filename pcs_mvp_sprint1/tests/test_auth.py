def test_login_returns_bearer_token(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "admin-change-me"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_invalid_login_is_rejected(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401
