from fastapi.testclient import TestClient


def test_not_found_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/missing")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Not Found",
        }
    }


def test_validation_error_uses_error_envelope(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get("/api/submissions", params={"page": 0}, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["message"]
