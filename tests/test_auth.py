from fastapi.testclient import TestClient


def test_login_returns_token_and_user(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "reviewer@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["accessToken"] == "dev-reviewer-token"
    assert body["tokenType"] == "Bearer"
    assert body["expiresIn"] == 900
    assert body["user"] == {
        "id": "c000000000000000000000001",
        "name": "Demo Reviewer",
        "email": "reviewer@example.com",
        "role": "reviewer",
    }


def test_login_returns_admin_user(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["accessToken"] == "dev-admin-token"
    assert body["tokenType"] == "Bearer"
    assert body["expiresIn"] == 900
    assert body["user"] == {
        "id": "c000000000000000000000002",
        "name": "Demo Admin",
        "email": "admin@example.com",
        "role": "admin",
    }


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "reviewer@example.com", "password": "wrongpass"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "invalid_credentials",
            "message": "Invalid email or password",
        }
    }


def test_me_requires_bearer_token(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_me_returns_current_user(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get("/api/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"]["email"] == "reviewer@example.com"


def test_me_returns_admin_user(client: TestClient) -> None:
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer dev-admin-token"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["email"] == "admin@example.com"
    assert response.json()["data"]["role"] == "admin"


def test_logout_returns_204(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post("/api/auth/logout", headers=auth_headers)

    assert response.status_code == 204
    assert response.content == b""
