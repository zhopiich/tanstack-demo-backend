from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.tokens import create_access_token
from app.main import create_app


@pytest.fixture(autouse=True)
def fast_password_hash_iterations(monkeypatch) -> None:
    monkeypatch.setenv("PASSWORD_HASH_ITERATIONS", "1")


@pytest.fixture
def client(tmp_path) -> Generator[TestClient]:
    app = create_app(database_path=tmp_path / "test.db")
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    access_token = create_access_token(
        claims={
            "sub": "c000000000000000000000001",
            "email": "reviewer@example.com",
            "name": "Reviewer User",
            "role": "reviewer",
        },
        secret_key="dev-secret-key-change-me",
        algorithm="HS256",
        expires_in_seconds=900,
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_headers() -> dict[str, str]:
    access_token = create_access_token(
        claims={
            "sub": "c000000000000000000000002",
            "email": "admin@example.com",
            "name": "Admin User",
            "role": "admin",
        },
        secret_key="dev-secret-key-change-me",
        algorithm="HS256",
        expires_in_seconds=900,
    )
    return {"Authorization": f"Bearer {access_token}"}
