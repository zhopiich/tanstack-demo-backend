from fastapi.testclient import TestClient


def test_dashboard_stats_returns_summary_breakdowns_and_activity(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get("/api/dashboard/stats", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["summary"] == {
        "totalSubmissions": 4,
        "pendingCount": 2,
        "approvedCount": 1,
        "rejectedCount": 0,
        "flaggedCount": 1,
    }
    assert {item["type"]: item["count"] for item in data["byType"]} == {
        "article": 1,
        "image": 1,
        "video": 1,
        "link": 1,
    }
    assert data["recentActivity"][0]["action"] in {
        "submitted",
        "approved",
        "rejected",
        "flagged",
    }
    assert data["topSubmitters"][0] == {
        "submitterId": "c100000000000000000000001",
        "name": "Alex Chen",
        "tier": "pro",
        "submissionCount": 2,
        "approvalRate": 0,
    }


def test_dashboard_stats_reflects_runtime_review_changes(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    listing = client.get("/api/submissions", headers=auth_headers).json()
    pending_id = next(
        item["id"] for item in listing["data"] if item["status"] == "pending"
    )

    reviewed = client.post(
        "/api/submissions/batch-review",
        json={
            "ids": [pending_id],
            "verdict": "approved",
            "reason": "This content is ready for publishing",
        },
        headers=auth_headers,
    )
    stats = client.get("/api/dashboard/stats", headers=auth_headers)

    assert reviewed.status_code == 200
    assert stats.status_code == 200
    summary = stats.json()["data"]["summary"]
    assert summary["pendingCount"] == 1
    assert summary["approvedCount"] == 2
    assert stats.json()["data"]["recentActivity"][0]["action"] == "approved"
