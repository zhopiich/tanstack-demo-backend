from collections import Counter, defaultdict
from typing import Literal

from app.schemas.dashboard import (
    DashboardByType,
    DashboardStats,
    DashboardSummary,
    RecentActivity,
    TopSubmitter,
)
from app.schemas.submission import Submission, SubmissionType
from app.stores.submission_store import InMemorySubmissionStore

SUBMISSION_TYPES: tuple[SubmissionType, ...] = ("article", "image", "video", "link")


class DashboardService:
    def __init__(self, store: InMemorySubmissionStore) -> None:
        self._store = store

    def stats(self) -> DashboardStats:
        submissions = self._store.list_submissions()
        status_counts = Counter(submission.status for submission in submissions)

        return DashboardStats(
            summary=DashboardSummary(
                totalSubmissions=len(submissions),
                pendingCount=status_counts["pending"],
                approvedCount=status_counts["approved"],
                rejectedCount=status_counts["rejected"],
                flaggedCount=status_counts["flagged"],
            ),
            byType=self._by_type(submissions),
            recentActivity=self._recent_activity(submissions),
            topSubmitters=self._top_submitters(submissions),
        )

    def _by_type(self, submissions: list[Submission]) -> list[DashboardByType]:
        counts_by_type = Counter(submission.content.type for submission in submissions)
        approved_by_type = Counter(
            submission.content.type
            for submission in submissions
            if submission.status == "approved"
        )

        return [
            DashboardByType(
                type=submission_type,
                count=counts_by_type[submission_type],
                approvalRate=(
                    approved_by_type[submission_type] / counts_by_type[submission_type]
                    if counts_by_type[submission_type]
                    else 0
                ),
            )
            for submission_type in SUBMISSION_TYPES
        ]

    def _recent_activity(self, submissions: list[Submission]) -> list[RecentActivity]:
        sorted_submissions = sorted(
            submissions,
            key=lambda submission: submission.updated_at,
            reverse=True,
        )

        return [
            RecentActivity(
                submissionId=submission.id,
                title=submission.title,
                action=self._activity_action(submission),
                actorName=self._activity_actor_name(submission),
                occurredAt=submission.updated_at,
            )
            for submission in sorted_submissions[:10]
        ]

    def _top_submitters(self, submissions: list[Submission]) -> list[TopSubmitter]:
        submissions_by_submitter: dict[str, list[Submission]] = defaultdict(list)
        for submission in submissions:
            submissions_by_submitter[submission.submitter.id].append(submission)

        submitters = [
            TopSubmitter(
                submitterId=group[0].submitter.id,
                name=group[0].submitter.name,
                tier=group[0].submitter.tier,
                submissionCount=len(group),
                approvalRate=self._approval_rate(group),
            )
            for group in submissions_by_submitter.values()
        ]

        return sorted(
            submitters,
            key=lambda submitter: (
                submitter.submission_count,
                submitter.approval_rate,
                submitter.name,
            ),
            reverse=True,
        )[:5]

    def _approval_rate(self, submissions: list[Submission]) -> float:
        if not submissions:
            return 0

        approved_count = sum(
            1 for submission in submissions if submission.status == "approved"
        )
        return approved_count / len(submissions)

    def _activity_action(
        self,
        submission: Submission,
    ) -> Literal["submitted", "approved", "rejected", "flagged"]:
        if submission.status in {"approved", "rejected", "flagged"}:
            return submission.status

        return "submitted"

    def _activity_actor_name(self, submission: Submission) -> str:
        if submission.review is not None:
            return submission.review.reviewer.name

        return submission.submitter.name
