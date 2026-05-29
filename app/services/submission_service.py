from datetime import UTC, datetime

from app.core.errors import ApiError
from app.schemas.common import Pagination
from app.schemas.submission import (
    ArticleContent,
    ImageContent,
    LinkContent,
    Submission,
    SubmissionListResponse,
    Submitter,
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

    def list_submissions(self) -> SubmissionListResponse:
        total = len(self._submissions)
        return SubmissionListResponse(
            data=self._submissions,
            pagination=Pagination(
                page=1,
                pageSize=20,
                total=total,
                totalPages=1 if total else 0,
            ),
        )

    def get_submission(self, submission_id: str) -> Submission:
        for submission in self._submissions:
            if submission.id == submission_id:
                return submission

        raise ApiError(404, "submission_not_found", "Submission not found")
