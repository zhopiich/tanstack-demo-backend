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
        connection.execute("SELECT COUNT(*) AS count FROM submissions")
        .fetchone()["count"]
        == 4
    )
    connection.close()


def test_create_app_keeps_existing_runtime_database(tmp_path) -> None:
    database_path = tmp_path / "runtime.db"
    first_app = create_app(database_path=database_path)
    with TestClient(first_app) as client:
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
            headers={"Authorization": "Bearer dev-reviewer-token"},
        )
    assert response.status_code == 201

    second_app = create_app(database_path=database_path)
    with TestClient(second_app) as client:
        listing = client.get(
            "/api/submissions",
            params={"search": "Persistent article"},
            headers={"Authorization": "Bearer dev-reviewer-token"},
        )

    assert listing.status_code == 200
    assert listing.json()["pagination"]["total"] == 1
