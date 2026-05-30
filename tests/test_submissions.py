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


def test_create_submission_persists_during_runtime(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    payload = {
        "title": "New article",
        "tags": ["news"],
        "content": {
            "type": "article",
            "url": "https://example.com/new-article",
            "thumbnailUrl": None,
            "wordCount": 1200,
            "readingTime": 6,
        },
        "submitterEmail": "alex@example.com",
    }

    created = client.post("/api/submissions", json=payload, headers=auth_headers)

    assert created.status_code == 201
    created_body = created.json()["data"]
    assert created_body["title"] == "New article"
    assert created_body["content"]["type"] == "article"
    assert "type" not in created_body

    fetched = client.get(f"/api/submissions/{created_body['id']}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == created_body["id"]


def test_create_submission_returns_404_for_unknown_submitter(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/submissions",
        json={
            "title": "Unknown submitter article",
            "tags": ["news"],
            "content": {
                "type": "article",
                "url": "https://example.com/unknown-submitter",
                "thumbnailUrl": None,
                "wordCount": 1200,
                "readingTime": 6,
            },
            "submitterEmail": "missing@example.com",
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "submitter_not_found",
            "message": "Submitter not found",
        }
    }


def test_patch_submission_updates_title_tags_and_content(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=auth_headers).json()
    submission_id = listing["data"][0]["id"]

    response = client.patch(
        f"/api/submissions/{submission_id}",
        json={"title": "Updated title", "tags": ["updated"]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Updated title"
    assert response.json()["data"]["tags"] == ["updated"]


def test_update_status_only_allows_pending_or_flagged(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=auth_headers).json()
    submission_id = listing["data"][0]["id"]

    flagged = client.patch(
        f"/api/submissions/{submission_id}/status",
        json={"status": "flagged"},
        headers=auth_headers,
    )
    rejected = client.patch(
        f"/api/submissions/{submission_id}/status",
        json={"status": "approved"},
        headers=auth_headers,
    )

    assert flagged.status_code == 200
    assert flagged.json()["data"]["status"] == "flagged"
    assert rejected.status_code == 422


def test_delete_submission_removes_it(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=auth_headers).json()
    submission_id = listing["data"][0]["id"]

    deleted = client.delete(f"/api/submissions/{submission_id}", headers=auth_headers)
    fetched = client.get(f"/api/submissions/{submission_id}", headers=auth_headers)

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert fetched.status_code == 404
