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


def test_list_submissions_filters_by_status_type_and_tier(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/submissions",
        params={"status": "pending", "type": "article", "tier": "pro"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 1
    assert body["data"][0]["status"] == "pending"
    assert body["data"][0]["content"]["type"] == "article"
    assert body["data"][0]["submitter"]["tier"] == "pro"
    assert body["pagination"]["total"] == 1


def test_list_submissions_searches_title_tags_and_submitter(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    title_match = client.get(
        "/api/submissions",
        params={"search": "walkthrough"},
        headers=auth_headers,
    )
    tag_match = client.get(
        "/api/submissions",
        params={"search": "research"},
        headers=auth_headers,
    )
    submitter_match = client.get(
        "/api/submissions",
        params={"search": "alex@example.com"},
        headers=auth_headers,
    )

    assert title_match.status_code == 200
    assert [item["title"] for item in title_match.json()["data"]] == [
        "Product walkthrough video"
    ]
    assert tag_match.status_code == 200
    assert [item["title"] for item in tag_match.json()["data"]] == [
        "External research link"
    ]
    assert submitter_match.status_code == 200
    assert submitter_match.json()["pagination"]["total"] == 2


def test_list_submissions_sorts_and_paginates(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/submissions",
        params={"sortBy": "score", "sortOrder": "desc", "page": 2, "pageSize": 2},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["score"] for item in body["data"]] == [73, 64]
    assert body["pagination"] == {
        "page": 2,
        "pageSize": 2,
        "total": 4,
        "totalPages": 2,
    }


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
    admin_headers: dict[str, str],
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

    created = client.post("/api/submissions", json=payload, headers=admin_headers)

    assert created.status_code == 201
    created_body = created.json()["data"]
    assert created_body["title"] == "New article"
    assert created_body["content"]["type"] == "article"
    assert "type" not in created_body

    fetched = client.get(
        f"/api/submissions/{created_body['id']}", headers=admin_headers
    )
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == created_body["id"]


def test_create_submission_returns_404_for_unknown_submitter(
    client: TestClient,
    admin_headers: dict[str, str],
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
        headers=admin_headers,
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
    admin_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=admin_headers).json()
    submission_id = listing["data"][0]["id"]

    response = client.patch(
        f"/api/submissions/{submission_id}",
        json={"title": "Updated title", "tags": ["updated"]},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Updated title"
    assert response.json()["data"]["tags"] == ["updated"]


def test_update_status_only_allows_pending_or_flagged(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=admin_headers).json()
    submission_id = listing["data"][0]["id"]

    flagged = client.patch(
        f"/api/submissions/{submission_id}/status",
        json={"status": "flagged"},
        headers=admin_headers,
    )
    rejected = client.patch(
        f"/api/submissions/{submission_id}/status",
        json={"status": "approved"},
        headers=admin_headers,
    )

    assert flagged.status_code == 200
    assert flagged.json()["data"]["status"] == "flagged"
    assert rejected.status_code == 422


def test_delete_submission_removes_it(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=admin_headers).json()
    submission_id = listing["data"][0]["id"]

    deleted = client.delete(f"/api/submissions/{submission_id}", headers=admin_headers)
    fetched = client.get(f"/api/submissions/{submission_id}", headers=admin_headers)

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert fetched.status_code == 404


def test_batch_review_updates_all_requested_submissions(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=auth_headers).json()
    ids = [item["id"] for item in listing["data"][:2]]

    response = client.post(
        "/api/submissions/batch-review",
        json={
            "ids": ids,
            "verdict": "rejected",
            "reason": "Does not satisfy the moderation policy",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"updatedCount": 2}

    for submission_id in ids:
        fetched = client.get(f"/api/submissions/{submission_id}", headers=auth_headers)
        data = fetched.json()["data"]
        assert data["status"] == "rejected"
        assert data["review"]["verdict"] == "rejected"
        assert data["review"]["reviewer"]["email"] == "reviewer@example.com"


def test_batch_review_is_all_or_nothing_when_an_id_is_missing(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=auth_headers).json()
    existing_id = listing["data"][0]["id"]

    response = client.post(
        "/api/submissions/batch-review",
        json={
            "ids": [existing_id, "c999999999999999999999999"],
            "verdict": "approved",
            "reason": "This content is ready for publishing",
        },
        headers=auth_headers,
    )

    fetched = client.get(f"/api/submissions/{existing_id}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "submission_not_found"
    assert fetched.json()["data"]["status"] == listing["data"][0]["status"]
    assert fetched.json()["data"]["review"] == listing["data"][0]["review"]


def test_batch_delete_removes_all_requested_submissions(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=admin_headers).json()
    ids = [item["id"] for item in listing["data"][:2]]

    response = client.post(
        "/api/submissions/batch-delete",
        json={"ids": ids},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"deletedCount": 2}

    for submission_id in ids:
        fetched = client.get(f"/api/submissions/{submission_id}", headers=admin_headers)
        assert fetched.status_code == 404


def test_create_submission_forbidden_for_reviewer(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/submissions",
        json={
            "title": "Reviewer attempt",
            "tags": ["test"],
            "content": {
                "type": "article",
                "url": "https://example.com/test",
                "thumbnailUrl": None,
                "wordCount": 100,
                "readingTime": 1,
            },
            "submitterEmail": "alex@example.com",
        },
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json() == {
        "error": {"code": "forbidden", "message": "Insufficient permissions"},
    }


def test_update_submission_forbidden_for_reviewer(
    client: TestClient,
    auth_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=admin_headers).json()
    submission_id = listing["data"][0]["id"]

    response = client.patch(
        f"/api/submissions/{submission_id}",
        json={"title": "Reviewer attempt"},
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json() == {
        "error": {"code": "forbidden", "message": "Insufficient permissions"},
    }


def test_delete_submission_forbidden_for_reviewer(
    client: TestClient,
    auth_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=admin_headers).json()
    submission_id = listing["data"][0]["id"]

    response = client.delete(
        f"/api/submissions/{submission_id}",
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json() == {
        "error": {"code": "forbidden", "message": "Insufficient permissions"},
    }


def test_batch_delete_forbidden_for_reviewer(
    client: TestClient,
    auth_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=admin_headers).json()
    ids = [item["id"] for item in listing["data"][:2]]

    response = client.post(
        "/api/submissions/batch-delete",
        json={"ids": ids},
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json() == {
        "error": {"code": "forbidden", "message": "Insufficient permissions"},
    }


def test_batch_review_allowed_for_reviewer(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=auth_headers).json()
    ids = [item["id"] for item in listing["data"][:2]]

    response = client.post(
        "/api/submissions/batch-review",
        json={
            "ids": ids,
            "verdict": "rejected",
            "reason": "Reviewer can review",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"updatedCount": 2}


def test_update_status_forbidden_for_reviewer(
    client: TestClient,
    auth_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=admin_headers).json()
    submission_id = listing["data"][0]["id"]

    response = client.patch(
        f"/api/submissions/{submission_id}/status",
        json={"status": "flagged"},
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json() == {
        "error": {"code": "forbidden", "message": "Insufficient permissions"},
    }
