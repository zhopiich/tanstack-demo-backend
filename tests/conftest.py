from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path) -> Generator[TestClient]:
    app = create_app(database_path=tmp_path / "test.db")
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": "reviewer@example.com", "password": "password123"},
    )
    access_token = response.json()["accessToken"]
    return {"Authorization": f"Bearer {access_token}"}
