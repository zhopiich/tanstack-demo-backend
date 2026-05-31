from datetime import UTC, datetime

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
from app.mappers.submission_mapper import to_domain_content, to_submission_schema
from app.schemas import submission as submission_schema


def test_maps_article_submission_domain_to_schema() -> None:
    timestamp = datetime(2026, 5, 29, 8, 0, tzinfo=UTC)
    submission = Submission(
        id="c200000000000000000000001",
        title="Article moderation guide",
        status=SubmissionStatus.PENDING,
        submitter=Submitter(
            id="c100000000000000000000001",
            name="Alex Chen",
            email="alex@example.com",
            tier=SubmitterTier.PRO,
        ),
        content=ArticleContent(
            url="https://example.com/articles/moderation-guide",
            thumbnail_url=None,
            word_count=1800,
            reading_time=9,
        ),
        tags=["editorial", "design"],
        review=Review(
            reviewer=Reviewer(name="Demo Reviewer", email="reviewer@example.com"),
            verdict=ReviewVerdict.APPROVED,
            reason="Looks good for publishing",
            reviewed_at=timestamp,
        ),
        score=82,
        flag_count=0,
        created_at=timestamp,
        updated_at=timestamp,
    )

    schema = to_submission_schema(submission)

    assert schema.model_dump(mode="json", by_alias=True) == {
        "id": "c200000000000000000000001",
        "title": "Article moderation guide",
        "status": "pending",
        "submitter": {
            "id": "c100000000000000000000001",
            "name": "Alex Chen",
            "email": "alex@example.com",
            "tier": "pro",
        },
        "content": {
            "type": "article",
            "url": "https://example.com/articles/moderation-guide",
            "thumbnailUrl": None,
            "wordCount": 1800,
            "readingTime": 9,
        },
        "tags": ["editorial", "design"],
        "review": {
            "reviewer": {
                "name": "Demo Reviewer",
                "email": "reviewer@example.com",
            },
            "verdict": "approved",
            "reason": "Looks good for publishing",
            "reviewedAt": "2026-05-29T08:00:00Z",
        },
        "score": 82,
        "flagCount": 0,
        "createdAt": "2026-05-29T08:00:00Z",
        "updatedAt": "2026-05-29T08:00:00Z",
    }


def test_maps_image_content_domain_to_schema() -> None:
    schema = to_submission_schema(
        _submission_with_content(
            ImageContent(
                url="https://example.com/images/launch-gallery",
                thumbnail_url="https://example.com/images/launch-thumb",
                width=1600,
                height=900,
            )
        )
    )

    assert schema.content.model_dump(mode="json", by_alias=True) == {
        "type": "image",
        "url": "https://example.com/images/launch-gallery",
        "thumbnailUrl": "https://example.com/images/launch-thumb",
        "width": 1600,
        "height": 900,
    }


def test_maps_video_content_domain_to_schema() -> None:
    schema = to_submission_schema(
        _submission_with_content(
            VideoContent(
                url="https://example.com/videos/product-walkthrough",
                thumbnail_url="https://example.com/videos/product-thumb",
                duration=420,
                resolution=VideoResolution.P1080,
            )
        )
    )

    assert schema.content.model_dump(mode="json", by_alias=True) == {
        "type": "video",
        "url": "https://example.com/videos/product-walkthrough",
        "thumbnailUrl": "https://example.com/videos/product-thumb",
        "duration": 420,
        "resolution": "1080p",
    }


def test_maps_link_content_domain_to_schema() -> None:
    schema = to_submission_schema(
        _submission_with_content(
            LinkContent(
                url="https://example.com/research/content-trends",
                thumbnail_url=None,
                domain="example.com",
                is_behind_paywall=False,
            )
        )
    )

    assert schema.content.model_dump(mode="json", by_alias=True) == {
        "type": "link",
        "url": "https://example.com/research/content-trends",
        "thumbnailUrl": None,
        "domain": "example.com",
        "isBehindPaywall": False,
    }


def test_maps_article_content_schema_to_domain() -> None:
    content = submission_schema.ArticleContent(
        type="article",
        url="https://example.com/articles/moderation-guide",
        thumbnailUrl=None,
        wordCount=1800,
        readingTime=9,
    )

    domain_content = to_domain_content(content)

    assert domain_content == ArticleContent(
        url="https://example.com/articles/moderation-guide",
        thumbnail_url=None,
        word_count=1800,
        reading_time=9,
    )


def test_maps_image_content_schema_to_domain() -> None:
    content = submission_schema.ImageContent(
        type="image",
        url="https://example.com/images/launch-gallery",
        thumbnailUrl="https://example.com/images/launch-thumb",
        width=1600,
        height=900,
    )

    domain_content = to_domain_content(content)

    assert domain_content == ImageContent(
        url="https://example.com/images/launch-gallery",
        thumbnail_url="https://example.com/images/launch-thumb",
        width=1600,
        height=900,
    )


def test_maps_video_content_schema_to_domain() -> None:
    content = submission_schema.VideoContent(
        type="video",
        url="https://example.com/videos/product-walkthrough",
        thumbnailUrl="https://example.com/videos/product-thumb",
        duration=420,
        resolution="1080p",
    )

    domain_content = to_domain_content(content)

    assert domain_content == VideoContent(
        url="https://example.com/videos/product-walkthrough",
        thumbnail_url="https://example.com/videos/product-thumb",
        duration=420,
        resolution=VideoResolution.P1080,
    )


def test_maps_link_content_schema_to_domain() -> None:
    content = submission_schema.LinkContent(
        type="link",
        url="https://example.com/research/content-trends",
        thumbnailUrl=None,
        domain="example.com",
        isBehindPaywall=False,
    )

    domain_content = to_domain_content(content)

    assert domain_content == LinkContent(
        url="https://example.com/research/content-trends",
        thumbnail_url=None,
        domain="example.com",
        is_behind_paywall=False,
    )


def _submission_with_content(
    content: ArticleContent | ImageContent | VideoContent | LinkContent,
) -> Submission:
    timestamp = datetime(2026, 5, 29, 8, 0, tzinfo=UTC)
    return Submission(
        id="c200000000000000000000001",
        title="Submission title",
        status=SubmissionStatus.PENDING,
        submitter=Submitter(
            id="c100000000000000000000001",
            name="Alex Chen",
            email="alex@example.com",
            tier=SubmitterTier.PRO,
        ),
        content=content,
        tags=["editorial"],
        review=None,
        score=82,
        flag_count=0,
        created_at=timestamp,
        updated_at=timestamp,
    )
