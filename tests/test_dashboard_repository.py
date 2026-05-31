from app.db.session import initialize_database
from app.repositories.dashboard_repository import DashboardRepository


def test_dashboard_repository_returns_summary_counts() -> None:
    repository = DashboardRepository(initialize_database())

    stats = repository.stats()

    assert stats.summary.total_submissions == 4
    assert stats.summary.pending_count == 2
    assert stats.summary.approved_count == 1
    assert stats.summary.rejected_count == 0
    assert stats.summary.flagged_count == 1


def test_dashboard_repository_returns_by_type_counts_and_approval_rates() -> None:
    repository = DashboardRepository(initialize_database())

    stats = repository.stats()

    assert [(item.type, item.count, item.approval_rate) for item in stats.by_type] == [
        ("article", 1, 0),
        ("image", 1, 1),
        ("video", 1, 0),
        ("link", 1, 0),
    ]


def test_dashboard_repository_returns_recent_activity() -> None:
    repository = DashboardRepository(initialize_database())

    stats = repository.stats()

    assert len(stats.recent_activity) == 4
    first = stats.recent_activity[0]
    assert first.submission_id == "c200000000000000000000001"
    assert first.title == "Article moderation guide"
    assert first.action == "submitted"
    assert first.actor_name == "Alex Chen"
    assert first.occurred_at.isoformat() == "2026-05-29T08:00:00+00:00"
    assert {activity.action for activity in stats.recent_activity} == {
        "submitted",
        "approved",
        "flagged",
    }


def test_dashboard_repository_returns_top_submitters() -> None:
    repository = DashboardRepository(initialize_database())

    stats = repository.stats()

    assert [
        (
            item.submitter_id,
            item.name,
            item.tier,
            item.submission_count,
            item.approval_rate,
        )
        for item in stats.top_submitters
    ] == [
        ("c100000000000000000000001", "Alex Chen", "pro", 2, 0),
        ("c100000000000000000000002", "Mina Lin", "verified", 1, 1),
        ("c100000000000000000000003", "Jordan Wu", "free", 1, 0),
    ]
