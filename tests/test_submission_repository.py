from dataclasses import replace
from datetime import UTC, datetime

from app.db.session import initialize_database
from app.domain.submission import (
    ArticleContent,
    ImageContent,
    LinkContent,
    Review,
    Reviewer,
    ReviewVerdict,
    Submission,
    SubmissionStatus,
    Submitter,
    SubmitterTier,
    VideoContent,
    VideoResolution,
)
from app.repositories.submission_repository import SubmissionRepository


def test_list_submissions_returns_seeded_domain_models() -> None:
    repository = SubmissionRepository(initialize_database())

    submissions = repository.list_submissions()

    assert [submission.id for submission in submissions] == [
        "c200000000000000000000001",
        "c200000000000000000000002",
        "c200000000000000000000003",
        "c200000000000000000000004",
    ]
    first = submissions[0]
    assert first.title == "Article moderation guide"
    assert first.status is SubmissionStatus.PENDING
    assert first.submitter.id == "c100000000000000000000001"
    assert first.submitter.name == "Alex Chen"
    assert first.submitter.email == "alex@example.com"
    assert first.submitter.tier is SubmitterTier.PRO
    assert first.tags == ["editorial", "design"]
    assert first.review is None
    assert first.score == 82
    assert first.flag_count == 0
    assert isinstance(first.content, ArticleContent)
    assert first.content.type.value == "article"
    assert first.content.url == "https://example.com/articles/moderation-guide"
    assert first.content.thumbnail_url is None
    assert first.content.word_count == 1800
    assert first.content.reading_time == 9
    assert first.created_at.isoformat() == "2026-05-29T08:00:00+00:00"
    assert first.updated_at.isoformat() == "2026-05-29T08:00:00+00:00"


def test_get_submission_returns_one_domain_model() -> None:
    repository = SubmissionRepository(initialize_database())

    submission = repository.get_submission("c200000000000000000000003")

    assert submission is not None
    assert submission.id == "c200000000000000000000003"
    assert submission.title == "Product walkthrough video"
    assert submission.status is SubmissionStatus.FLAGGED
    assert isinstance(submission.content, VideoContent)
    assert submission.content.duration == 420
    assert submission.content.resolution is VideoResolution.P1080
    assert submission.tags == ["product", "video"]


def test_get_submission_returns_none_for_missing_id() -> None:
    repository = SubmissionRepository(initialize_database())

    submission = repository.get_submission("c999999999999999999999999")

    assert submission is None


def test_get_submitter_by_email_returns_domain_submitter() -> None:
    repository = SubmissionRepository(initialize_database())

    submitter = repository.get_submitter_by_email("mina@example.com")

    assert submitter is not None
    assert submitter.id == "c100000000000000000000002"
    assert submitter.name == "Mina Lin"
    assert submitter.email == "mina@example.com"
    assert submitter.tier is SubmitterTier.VERIFIED


def test_get_submitter_by_email_returns_none_for_missing_email() -> None:
    repository = SubmissionRepository(initialize_database())

    submitter = repository.get_submitter_by_email("missing@example.com")

    assert submitter is None


def test_list_submissions_maps_all_content_variants() -> None:
    repository = SubmissionRepository(initialize_database())

    submissions = repository.list_submissions()

    image = submissions[1]
    assert isinstance(image.content, ImageContent)
    assert image.content.width == 1600
    assert image.content.height == 900
    assert image.content.thumbnail_url == "https://example.com/images/launch-thumb"

    video = submissions[2]
    assert isinstance(video.content, VideoContent)
    assert video.content.duration == 420
    assert video.content.resolution is VideoResolution.P1080

    link = submissions[3]
    assert isinstance(link.content, LinkContent)
    assert link.content.domain == "example.com"
    assert link.content.is_behind_paywall is False


def test_add_submission_persists_complete_domain_model() -> None:
    repository = SubmissionRepository(initialize_database())
    timestamp = datetime(2026, 5, 31, 10, 0, tzinfo=UTC)
    submission = Submission(
        id="c200000000000000000000099",
        title="New backend article",
        status=SubmissionStatus.PENDING,
        submitter=Submitter(
            id="c100000000000000000000001",
            name="Alex Chen",
            email="alex@example.com",
            tier=SubmitterTier.PRO,
        ),
        content=ArticleContent(
            url="https://example.com/articles/new-backend-article",
            thumbnail_url=None,
            word_count=1200,
            reading_time=6,
        ),
        tags=["backend", "sqlite"],
        review=None,
        score=0,
        flag_count=0,
        created_at=timestamp,
        updated_at=timestamp,
    )

    created = repository.add_submission(submission)

    assert created == submission
    persisted = repository.get_submission("c200000000000000000000099")
    assert persisted == submission
    assert [item.id for item in repository.list_submissions()][-1] == submission.id


def test_update_submission_replaces_tags_content_and_review() -> None:
    repository = SubmissionRepository(initialize_database())
    timestamp = datetime(2026, 5, 31, 11, 0, tzinfo=UTC)
    original = repository.get_submission("c200000000000000000000001")
    assert original is not None
    updated = replace(
        original,
        title="Updated launch image",
        status=SubmissionStatus.APPROVED,
        content=ImageContent(
            url="https://example.com/images/updated-launch",
            thumbnail_url="https://example.com/images/updated-launch-thumb",
            width=1200,
            height=800,
        ),
        tags=["updated", "image"],
        review=Review(
            reviewer=Reviewer(
                name="Admin User",
                email="admin@example.com",
            ),
            verdict=ReviewVerdict.APPROVED,
            reason="Approved after editorial review",
            reviewed_at=timestamp,
        ),
        score=91,
        flag_count=2,
        updated_at=timestamp,
    )

    saved = repository.update_submission(updated)

    assert saved == updated
    persisted = repository.get_submission("c200000000000000000000001")
    assert persisted == updated
    assert isinstance(persisted.content, ImageContent)
    assert persisted.tags == ["updated", "image"]
    assert persisted.review is not None
    assert persisted.review.reviewer.email == "admin@example.com"


def test_update_submission_returns_none_for_missing_submission() -> None:
    repository = SubmissionRepository(initialize_database())
    missing = _new_link_submission("c200000000000000000000099")

    result = repository.update_submission(missing)

    assert result is None


def test_delete_submission_removes_submission_and_child_rows() -> None:
    repository = SubmissionRepository(initialize_database())

    deleted = repository.delete_submission("c200000000000000000000003")

    assert deleted is True
    assert repository.get_submission("c200000000000000000000003") is None
    assert [submission.id for submission in repository.list_submissions()] == [
        "c200000000000000000000001",
        "c200000000000000000000002",
        "c200000000000000000000004",
    ]


def test_delete_submission_returns_false_for_missing_submission() -> None:
    repository = SubmissionRepository(initialize_database())

    deleted = repository.delete_submission("c999999999999999999999999")

    assert deleted is False


def _new_link_submission(submission_id: str) -> Submission:
    timestamp = datetime(2026, 5, 31, 12, 0, tzinfo=UTC)
    return Submission(
        id=submission_id,
        title="New reference link",
        status=SubmissionStatus.PENDING,
        submitter=Submitter(
            id="c100000000000000000000001",
            name="Alex Chen",
            email="alex@example.com",
            tier=SubmitterTier.PRO,
        ),
        content=LinkContent(
            url="https://example.com/reference/new-link",
            thumbnail_url=None,
            domain="example.com",
            is_behind_paywall=False,
        ),
        tags=["reference"],
        review=None,
        score=0,
        flag_count=0,
        created_at=timestamp,
        updated_at=timestamp,
    )
