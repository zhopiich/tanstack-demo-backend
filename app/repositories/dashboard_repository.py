import sqlite3
from datetime import datetime
from typing import Literal

from app.read_models.dashboard import (
    DashboardByTypeReadModel,
    DashboardStatsReadModel,
    DashboardSummaryReadModel,
    RecentActivityReadModel,
    TopSubmitterReadModel,
)

SUBMISSION_TYPES = ("article", "image", "video", "link")


class DashboardRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def stats(self) -> DashboardStatsReadModel:
        return DashboardStatsReadModel(
            summary=self._summary(),
            by_type=self._by_type(),
            recent_activity=self._recent_activity(),
            top_submitters=self._top_submitters(),
        )

    def _summary(self) -> DashboardSummaryReadModel:
        row = self._connection.execute(
            """
            SELECT
                COUNT(*) AS total_submissions,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END)
                    AS pending_count,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END)
                    AS approved_count,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END)
                    AS rejected_count,
                SUM(CASE WHEN status = 'flagged' THEN 1 ELSE 0 END)
                    AS flagged_count
            FROM submissions
            """
        ).fetchone()
        return DashboardSummaryReadModel(
            total_submissions=row["total_submissions"],
            pending_count=row["pending_count"],
            approved_count=row["approved_count"],
            rejected_count=row["rejected_count"],
            flagged_count=row["flagged_count"],
        )

    def _by_type(self) -> list[DashboardByTypeReadModel]:
        rows = self._connection.execute(
            """
            SELECT
                content_type,
                COUNT(*) AS submission_count,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END)
                    AS approved_count
            FROM submissions
            GROUP BY content_type
            """
        ).fetchall()
        rows_by_type = {row["content_type"]: row for row in rows}

        results: list[DashboardByTypeReadModel] = []
        for submission_type in SUBMISSION_TYPES:
            row = rows_by_type.get(submission_type)
            count = row["submission_count"] if row else 0
            approved_count = row["approved_count"] if row else 0
            results.append(
                DashboardByTypeReadModel(
                    type=submission_type,
                    count=count,
                    approval_rate=approved_count / count if count else 0,
                )
            )
        return results

    def _recent_activity(self) -> list[RecentActivityReadModel]:
        rows = self._connection.execute(
            """
            SELECT
                submissions.id,
                submissions.title,
                submissions.status,
                submissions.updated_at,
                submitters.name AS submitter_name,
                reviews.reviewer_name
            FROM submissions
            JOIN submitters ON submitters.id = submissions.submitter_id
            LEFT JOIN reviews ON reviews.submission_id = submissions.id
            ORDER BY submissions.updated_at DESC, submissions.id ASC
            LIMIT 10
            """
        ).fetchall()

        return [
            RecentActivityReadModel(
                submission_id=row["id"],
                title=row["title"],
                action=self._activity_action(row["status"]),
                actor_name=row["reviewer_name"] or row["submitter_name"],
                occurred_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    def _activity_action(
        self, status: str
    ) -> Literal["submitted", "approved", "rejected", "flagged"]:
        if status in {"approved", "rejected", "flagged"}:
            return status
        return "submitted"

    def _top_submitters(self) -> list[TopSubmitterReadModel]:
        rows = self._connection.execute(
            """
            SELECT
                submitters.id,
                submitters.name,
                submitters.tier,
                COUNT(submissions.id) AS submission_count,
                SUM(CASE WHEN submissions.status = 'approved' THEN 1 ELSE 0 END)
                    AS approved_count
            FROM submitters
            JOIN submissions ON submissions.submitter_id = submitters.id
            GROUP BY submitters.id, submitters.name, submitters.tier
            ORDER BY
                submission_count DESC,
                approved_count * 1.0 / submission_count DESC,
                submitters.name DESC
            LIMIT 5
            """
        ).fetchall()

        return [
            TopSubmitterReadModel(
                submitter_id=row["id"],
                name=row["name"],
                tier=row["tier"],
                submission_count=row["submission_count"],
                approval_rate=(
                    row["approved_count"] / row["submission_count"]
                    if row["submission_count"]
                    else 0
                ),
            )
            for row in rows
        ]
