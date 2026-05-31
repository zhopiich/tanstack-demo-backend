from app.db.session import initialize_database
from app.domain.submission import (
    ArticleContent,
    ImageContent,
    LinkContent,
    SubmissionStatus,
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
