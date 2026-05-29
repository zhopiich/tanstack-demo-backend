from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> Generator[TestClient]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
