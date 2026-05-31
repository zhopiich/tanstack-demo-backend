from datetime import UTC, datetime

from app.mappers.dashboard_mapper import to_dashboard_stats_schema
from app.read_models.dashboard import (
    DashboardByTypeReadModel,
    DashboardStatsReadModel,
    DashboardSummaryReadModel,
    RecentActivityReadModel,
    TopSubmitterReadModel,
)


def test_maps_dashboard_stats_read_model_to_schema() -> None:
    timestamp = datetime(2026, 5, 29, 8, 0, tzinfo=UTC)
    read_model = DashboardStatsReadModel(
        summary=DashboardSummaryReadModel(
            total_submissions=4,
            pending_count=2,
            approved_count=1,
            rejected_count=0,
            flagged_count=1,
        ),
        by_type=[
            DashboardByTypeReadModel(
                type="article",
                count=2,
                approval_rate=0.5,
            ),
            DashboardByTypeReadModel(
                type="image",
                count=1,
                approval_rate=1,
            ),
        ],
        recent_activity=[
            RecentActivityReadModel(
                submission_id="c200000000000000000000001",
                title="Article moderation guide",
                action="submitted",
                actor_name="Alex Chen",
                occurred_at=timestamp,
            )
        ],
        top_submitters=[
            TopSubmitterReadModel(
                submitter_id="c100000000000000000000001",
                name="Alex Chen",
                tier="pro",
                submission_count=2,
                approval_rate=0.5,
            )
        ],
    )

    schema = to_dashboard_stats_schema(read_model)

    assert schema.model_dump(mode="json", by_alias=True) == {
        "summary": {
            "totalSubmissions": 4,
            "pendingCount": 2,
            "approvedCount": 1,
            "rejectedCount": 0,
            "flaggedCount": 1,
        },
        "byType": [
            {
                "type": "article",
                "count": 2,
                "approvalRate": 0.5,
            },
            {
                "type": "image",
                "count": 1,
                "approvalRate": 1.0,
            },
        ],
        "recentActivity": [
            {
                "submissionId": "c200000000000000000000001",
                "title": "Article moderation guide",
                "action": "submitted",
                "actorName": "Alex Chen",
                "occurredAt": "2026-05-29T08:00:00Z",
            }
        ],
        "topSubmitters": [
            {
                "submitterId": "c100000000000000000000001",
                "name": "Alex Chen",
                "tier": "pro",
                "submissionCount": 2,
                "approvalRate": 0.5,
            }
        ],
    }


def test_maps_empty_dashboard_lists_to_schema() -> None:
    read_model = DashboardStatsReadModel(
        summary=DashboardSummaryReadModel(
            total_submissions=0,
            pending_count=0,
            approved_count=0,
            rejected_count=0,
            flagged_count=0,
        ),
        by_type=[],
        recent_activity=[],
        top_submitters=[],
    )

    schema = to_dashboard_stats_schema(read_model)

    assert schema.model_dump(mode="json", by_alias=True) == {
        "summary": {
            "totalSubmissions": 0,
            "pendingCount": 0,
            "approvedCount": 0,
            "rejectedCount": 0,
            "flaggedCount": 0,
        },
        "byType": [],
        "recentActivity": [],
        "topSubmitters": [],
    }
