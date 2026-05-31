from app.domain import submission as domain
from app.schemas import submission as schema


def to_submission_schema(submission: domain.Submission) -> schema.Submission:
    return schema.Submission(
        id=submission.id,
        title=submission.title,
        status=submission.status.value,
        submitter=_to_submitter_schema(submission.submitter),
        content=_to_content_schema(submission.content),
        tags=submission.tags,
        review=_to_review_schema(submission.review),
        score=submission.score,
        flagCount=submission.flag_count,
        createdAt=submission.created_at,
        updatedAt=submission.updated_at,
    )


def to_domain_content(content: schema.Content) -> domain.Content:
    thumbnail_url = str(content.thumbnail_url) if content.thumbnail_url else None

    if isinstance(content, schema.ArticleContent):
        return domain.ArticleContent(
            url=str(content.url),
            thumbnail_url=thumbnail_url,
            word_count=content.word_count,
            reading_time=content.reading_time,
        )

    if isinstance(content, schema.ImageContent):
        return domain.ImageContent(
            url=str(content.url),
            thumbnail_url=thumbnail_url,
            width=content.width,
            height=content.height,
        )

    if isinstance(content, schema.VideoContent):
        return domain.VideoContent(
            url=str(content.url),
            thumbnail_url=thumbnail_url,
            duration=content.duration,
            resolution=domain.VideoResolution(content.resolution),
        )

    return domain.LinkContent(
        url=str(content.url),
        thumbnail_url=thumbnail_url,
        domain=content.domain,
        is_behind_paywall=content.is_behind_paywall,
    )


def _to_submitter_schema(submitter: domain.Submitter) -> schema.Submitter:
    return schema.Submitter(
        id=submitter.id,
        name=submitter.name,
        email=submitter.email,
        tier=submitter.tier.value,
    )


def _to_content_schema(content: domain.Content) -> schema.Content:
    if isinstance(content, domain.ArticleContent):
        return schema.ArticleContent(
            type=content.type.value,
            url=content.url,
            thumbnailUrl=content.thumbnail_url,
            wordCount=content.word_count,
            readingTime=content.reading_time,
        )

    if isinstance(content, domain.ImageContent):
        return schema.ImageContent(
            type=content.type.value,
            url=content.url,
            thumbnailUrl=content.thumbnail_url,
            width=content.width,
            height=content.height,
        )

    if isinstance(content, domain.VideoContent):
        return schema.VideoContent(
            type=content.type.value,
            url=content.url,
            thumbnailUrl=content.thumbnail_url,
            duration=content.duration,
            resolution=content.resolution.value,
        )

    return schema.LinkContent(
        type=content.type.value,
        url=content.url,
        thumbnailUrl=content.thumbnail_url,
        domain=content.domain,
        isBehindPaywall=content.is_behind_paywall,
    )


def _to_review_schema(review: domain.Review | None) -> schema.Review | None:
    if review is None:
        return None

    return schema.Review(
        reviewer=schema.Reviewer(
            name=review.reviewer.name,
            email=review.reviewer.email,
        ),
        verdict=review.verdict.value,
        reason=review.reason,
        reviewedAt=review.reviewed_at,
    )
