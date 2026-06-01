from fastapi.testclient import TestClient

from app.db.session import connect_database
from app.main import create_app


def test_create_app_initializes_missing_runtime_database(tmp_path) -> None:
    database_path = tmp_path / "runtime.db"

    app = create_app(database_path=database_path)

    assert app.state.settings.database_path == database_path
    assert database_path.exists()
    connection = connect_database(database_path)
    assert (
        connection.execute("SELECT COUNT(*) AS count FROM submissions").fetchone()[
            "count"
        ]
        == 4
    )
    connection.close()


def test_create_app_database_path_override_preserves_other_settings(
    monkeypatch,
    tmp_path,
) -> None:
    database_path = tmp_path / "runtime.db"
    monkeypatch.setenv("JWT_SECRET_KEY", "env-secret")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRES_SECONDS", "60")

    app = create_app(database_path=database_path)

    assert app.state.settings.database_path == database_path
    assert app.state.settings.jwt_secret_key == "env-secret"
    assert app.state.settings.access_token_expires_seconds == 60


def test_create_app_keeps_existing_runtime_database(tmp_path) -> None:
    database_path = tmp_path / "runtime.db"
    first_app = create_app(database_path=database_path)
    with TestClient(first_app) as client:
        login = client.post(
            "/api/auth/login",
            json={"email": "reviewer@example.com", "password": "password123"},
        )
        auth_headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
        response = client.post(
            "/api/submissions",
            json={
                "title": "Persistent article",
                "tags": ["runtime"],
                "content": {
                    "type": "article",
                    "url": "https://example.com/persistent",
                    "thumbnailUrl": None,
                    "wordCount": 1200,
                    "readingTime": 6,
                },
                "submitterEmail": "alex@example.com",
            },
            headers=auth_headers,
        )
    assert response.status_code == 201

    second_app = create_app(database_path=database_path)
    with TestClient(second_app) as client:
        login = client.post(
            "/api/auth/login",
            json={"email": "reviewer@example.com", "password": "password123"},
        )
        auth_headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
        listing = client.get(
            "/api/submissions",
            params={"search": "Persistent article"},
            headers=auth_headers,
        )

    assert listing.status_code == 200
    assert listing.json()["pagination"]["total"] == 1
