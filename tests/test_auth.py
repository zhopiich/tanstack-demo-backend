from fastapi.testclient import TestClient


def test_login_returns_access_token_user_and_refresh_cookie(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "reviewer@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"user", "accessToken", "tokenType", "expiresIn"}
    assert body["accessToken"]
    assert body["tokenType"] == "Bearer"
    assert body["expiresIn"] == 900
    assert body["user"] == {
        "id": "c000000000000000000000001",
        "name": "Reviewer User",
        "email": "reviewer@example.com",
        "role": "reviewer",
    }
    assert "refresh_token=" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "Path=/api/auth" in response.headers["set-cookie"]


def test_login_returns_admin_user(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["accessToken"]
    assert body["tokenType"] == "Bearer"
    assert body["expiresIn"] == 900
    assert body["user"] == {
        "id": "c000000000000000000000002",
        "name": "Admin User",
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
    assert response.json()["data"]["role"] == "reviewer"


def test_me_rejects_invalid_access_token(client: TestClient) -> None:
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_refresh_returns_access_token_and_rotates_refresh_cookie(
    client: TestClient,
) -> None:
    client.post(
        "/api/auth/login",
        json={"email": "reviewer@example.com", "password": "password123"},
    )
    old_refresh_token = client.cookies.get("refresh_token")

    response = client.post("/api/auth/refresh")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"user", "accessToken", "tokenType", "expiresIn"}
    assert body["accessToken"]
    assert body["tokenType"] == "Bearer"
    assert body["expiresIn"] == 900
    assert body["user"]["email"] == "reviewer@example.com"
    assert client.cookies.get("refresh_token") != old_refresh_token
    assert "refresh_token=" in response.headers["set-cookie"]


def test_refresh_rejects_rotated_refresh_token(client: TestClient) -> None:
    client.post(
        "/api/auth/login",
        json={"email": "reviewer@example.com", "password": "password123"},
    )
    old_refresh_token = client.cookies.get("refresh_token")
    assert old_refresh_token is not None
    assert client.post("/api/auth/refresh").status_code == 200

    client.cookies.set("refresh_token", old_refresh_token, path="/api/auth")
    response = client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Invalid refresh token",
        }
    }


def test_refresh_requires_refresh_cookie(client: TestClient) -> None:
    response = client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Invalid refresh token",
        }
    }


def test_me_returns_admin_user(client: TestClient) -> None:
    login = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "password123"},
    )
    access_token = login.json()["accessToken"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["email"] == "admin@example.com"
    assert response.json()["data"]["role"] == "admin"


def test_logout_returns_204_revokes_refresh_and_clears_cookie(
    client: TestClient,
) -> None:
    client.post(
        "/api/auth/login",
        json={"email": "reviewer@example.com", "password": "password123"},
    )

    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    assert response.content == b""
    assert "refresh_token=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]

    refresh = client.post("/api/auth/refresh")
    assert refresh.status_code == 401


def test_logout_without_refresh_cookie_still_returns_204(
    client: TestClient,
) -> None:
    client.cookies.clear()

    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    assert response.content == b""
