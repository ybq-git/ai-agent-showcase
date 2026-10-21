from tests.conftest import auth


def test_register_login_and_me(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "alice123",
            "role": "buyer",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["role"] == "buyer"

    login = client.post("/api/auth/login", data={"username": "alice", "password": "alice123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/auth/me", headers=auth(token))
    assert me.status_code == 200
    assert me.json()["username"] == "alice"


def test_duplicate_username_rejected(client):
    payload = {
        "username": "bob",
        "email": "bob@example.com",
        "password": "bob12345",
        "role": "buyer",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    duplicate = client.post(
        "/api/auth/register",
        json={**payload, "email": "bob2@example.com"},
    )
    assert duplicate.status_code == 400


def test_cannot_register_as_admin(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "hacker",
            "email": "hacker@example.com",
            "password": "hacker123",
            "role": "admin",
        },
    )
    assert response.status_code == 422
