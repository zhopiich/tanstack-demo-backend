from datetime import UTC, datetime
from math import ceil
from typing import Literal

from app.core.errors import ApiError
from app.schemas.auth import AuthUser
from app.schemas.common import Pagination
from app.schemas.submission import (
    ArticleContent,
    BatchDeleteBody,
    BatchReviewBody,
    DeletedCountResponse,
    ImageContent,
    LinkContent,
    Review,
    Reviewer,
    SortOrder,
    Submission,
    SubmissionCreateBody,
    SubmissionListResponse,
    SubmissionStatus,
    SubmissionStatusUpdateBody,
    SubmissionType,
    SubmissionUpdateBody,
    Submitter,
    SubmitterTier,
    UpdatedCountResponse,
    VideoContent,
)


def seed_submissions() -> list[Submission]:
    now = datetime(2026, 5, 29, 8, 0, tzinfo=UTC)
    submitters = [
        Submitter(
            id="c100000000000000000000001",
            name="Alex Chen",
            email="alex@example.com",
            tier="pro",
        ),
        Submitter(
            id="c100000000000000000000002",
            name="Mina Lin",
            email="mina@example.com",
            tier="verified",
        ),
        Submitter(
            id="c100000000000000000000003",
            name="Jordan Wu",
            email="jordan@example.com",
            tier="free",
        ),
    ]

    return [
        Submission(
            id="c200000000000000000000001",
            title="Article moderation guide",
            status="pending",
            submitter=submitters[0],
            content=ArticleContent(
                type="article",
                url="https://example.com/articles/moderation-guide",
                thumbnailUrl=None,
                wordCount=1800,
                readingTime=9,
            ),
            tags=["editorial", "design"],
            review=None,
            score=82,
            flagCount=0,
            createdAt=now,
            updatedAt=now,
        ),
        Submission(
            id="c200000000000000000000002",
            title="Launch image gallery",
            status="approved",
            submitter=submitters[1],
            content=ImageContent(
                type="image",
                url="https://example.com/images/launch-gallery",
                thumbnailUrl="https://example.com/images/launch-thumb",
                width=1600,
                height=900,
            ),
            tags=["launch", "visual"],
            review=None,
            score=91,
            flagCount=1,
            createdAt=now,
            updatedAt=now,
        ),
        Submission(
            id="c200000000000000000000003",
            title="Product walkthrough video",
            status="flagged",
            submitter=submitters[0],
            content=VideoContent(
                type="video",
                url="https://example.com/videos/product-walkthrough",
                thumbnailUrl="https://example.com/videos/product-thumb",
                duration=420,
                resolution="1080p",
            ),
            tags=["product", "video"],
            review=None,
            score=64,
            flagCount=3,
            createdAt=now,
            updatedAt=now,
        ),
        Submission(
            id="c200000000000000000000004",
            title="External research link",
            status="pending",
            submitter=submitters[2],
            content=LinkContent(
                type="link",
                url="https://example.com/research/content-trends",
                thumbnailUrl=None,
                domain="example.com",
                isBehindPaywall=False,
            ),
            tags=["research"],
            review=None,
            score=73,
            flagCount=0,
            createdAt=now,
            updatedAt=now,
        ),
    ]


class SubmissionService:
    def __init__(self) -> None:
        self._submissions = seed_submissions()
        self._next_id = 5
        self._submitters = {
            str(submission.submitter.email): submission.submitter
            for submission in self._submissions
        }

    def list_submissions(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: SubmissionStatus | None = None,
        type_: SubmissionType | None = None,
        tier: SubmitterTier | None = None,
        search: str | None = None,
        sort_by: Literal["createdAt", "score", "flagCount"] = "createdAt",
        sort_order: SortOrder = "desc",
    ) -> SubmissionListResponse:
        query = search.strip().lower() if search else None
        submissions = [
            submission
            for submission in self._submissions
            if self._matches_filters(
                submission,
                status=status,
                type_=type_,
                tier=tier,
                query=query,
            )
        ]

        submissions.sort(
            key=lambda submission: self._sort_value(submission, sort_by),
            reverse=sort_order == "desc",
        )

        total = len(submissions)
        start = (page - 1) * page_size
        end = start + page_size

        return SubmissionListResponse(
            data=submissions[start:end],
            pagination=Pagination(
                page=page,
                pageSize=page_size,
                total=total,
                totalPages=ceil(total / page_size) if total else 0,
            ),
        )

    def get_submission(self, submission_id: str) -> Submission:
        for submission in self._submissions:
            if submission.id == submission_id:
                return submission

        raise ApiError(404, "submission_not_found", "Submission not found")

    def create_submission(self, body: SubmissionCreateBody) -> Submission:
        now = datetime.now(UTC)
        submission = Submission(
            id=self._generate_id(),
            title=body.title,
            status="pending",
            submitter=self._submitter_for_email(str(body.submitter_email)),
            content=body.content,
            tags=body.tags,
            review=None,
            score=0,
            flagCount=0,
            createdAt=now,
            updatedAt=now,
        )
        self._submissions.append(submission)
        return submission

    def update_submission(
        self,
        submission_id: str,
        body: SubmissionUpdateBody,
    ) -> Submission:
        submission = self.get_submission(submission_id)
        update_data = body.model_dump(exclude_unset=True)

        if "title" in update_data:
            submission.title = body.title or submission.title
        if "tags" in update_data:
            submission.tags = body.tags or []
        if "content" in update_data and body.content is not None:
            submission.content = body.content

        submission.updated_at = datetime.now(UTC)
        return submission

    def update_status(
        self,
        submission_id: str,
        body: SubmissionStatusUpdateBody,
    ) -> Submission:
        submission = self.get_submission(submission_id)
        submission.status = body.status
        submission.updated_at = datetime.now(UTC)
        return submission

    def delete_submission(self, submission_id: str) -> None:
        submission = self.get_submission(submission_id)
        self._submissions.remove(submission)

    def batch_review(
        self,
        body: BatchReviewBody,
        reviewer: AuthUser,
    ) -> UpdatedCountResponse:
        submissions = self._submissions_by_ids(body.ids)
        now = datetime.now(UTC)

        for submission in submissions:
            submission.status = body.verdict
            submission.review = Review(
                reviewer=Reviewer(name=reviewer.name, email=reviewer.email),
                verdict=body.verdict,
                reason=body.reason,
                reviewedAt=now,
            )
            submission.updated_at = now

        return UpdatedCountResponse(updatedCount=len(submissions))

    def batch_delete(self, body: BatchDeleteBody) -> DeletedCountResponse:
        submissions = self._submissions_by_ids(body.ids)

        for submission in submissions:
            self._submissions.remove(submission)

        return DeletedCountResponse(deletedCount=len(submissions))

    def _generate_id(self) -> str:
        value = self._next_id
        self._next_id += 1
        return f"c{value:024x}"

    def _submitter_for_email(self, email: str) -> Submitter:
        submitter = self._submitters.get(email)
        if submitter is None:
            raise ApiError(404, "submitter_not_found", "Submitter not found")

        return submitter

    def _submissions_by_ids(self, ids: list[str]) -> list[Submission]:
        unique_ids = list(dict.fromkeys(ids))
        submissions_by_id = {
            submission.id: submission
            for submission in self._submissions
            if submission.id in unique_ids
        }

        for submission_id in unique_ids:
            if submission_id not in submissions_by_id:
                raise ApiError(404, "submission_not_found", "Submission not found")

        return [submissions_by_id[submission_id] for submission_id in unique_ids]

    def _matches_filters(
        self,
        submission: Submission,
        *,
        status: SubmissionStatus | None,
        type_: SubmissionType | None,
        tier: SubmitterTier | None,
        query: str | None,
    ) -> bool:
        return (
            (status is None or submission.status == status)
            and (type_ is None or submission.content.type == type_)
            and (tier is None or submission.submitter.tier == tier)
            and (not query or self._matches_search(submission, query))
        )

    def _matches_search(self, submission: Submission, query: str) -> bool:
        searchable_values = [
            submission.title,
            *submission.tags,
            submission.submitter.name,
            str(submission.submitter.email),
        ]
        return any(query in value.lower() for value in searchable_values)

    def _sort_value(
        self,
        submission: Submission,
        sort_by: Literal["createdAt", "score", "flagCount"],
    ) -> datetime | int:
        if sort_by == "createdAt":
            return submission.created_at
        if sort_by == "score":
            return submission.score

        return submission.flag_count
