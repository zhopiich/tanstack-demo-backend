from fastapi.testclient import TestClient


def test_list_submissions_returns_paginated_data(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get("/api/submissions", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) >= 4
    assert body["pagination"] == {
        "page": 1,
        "pageSize": 20,
        "total": len(body["data"]),
        "totalPages": 1,
    }
    assert "type" not in body["data"][0]
    assert body["data"][0]["content"]["type"] in {"article", "image", "video", "link"}


def test_get_submission_by_id(client: TestClient, auth_headers: dict[str, str]) -> None:
    listing = client.get("/api/submissions", headers=auth_headers).json()
    submission_id = listing["data"][0]["id"]

    response = client.get(f"/api/submissions/{submission_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"]["id"] == submission_id


def test_get_submission_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/submissions/c999999999999999999999999",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "submission_not_found",
            "message": "Submission not found",
        }
    }
