import sqlite3

from app.schemas.submission import (
    ArticleContent,
    ImageContent,
    LinkContent,
    VideoContent,
)
from app.stores.submission_store import seed_submissions


def seed_database(connection: sqlite3.Connection) -> None:
    submissions = seed_submissions()
    submitters_by_id = {
        submission.submitter.id: submission.submitter for submission in submissions
    }

    connection.executemany(
        """
        INSERT INTO submitters (id, name, email, tier)
        VALUES (:id, :name, :email, :tier)
        """,
        [
            {
                "id": submitter.id,
                "name": submitter.name,
                "email": str(submitter.email),
                "tier": submitter.tier,
            }
            for submitter in submitters_by_id.values()
        ],
    )

    for submission in submissions:
        connection.execute(
            """
            INSERT INTO submissions (
                id,
                title,
                status,
                submitter_id,
                content_type,
                content_url,
                thumbnail_url,
                score,
                flag_count,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :title,
                :status,
                :submitter_id,
                :content_type,
                :content_url,
                :thumbnail_url,
                :score,
                :flag_count,
                :created_at,
                :updated_at
            )
            """,
            {
                "id": submission.id,
                "title": submission.title,
                "status": submission.status,
                "submitter_id": submission.submitter.id,
                "content_type": submission.content.type,
                "content_url": str(submission.content.url),
                "thumbnail_url": (
                    str(submission.content.thumbnail_url)
                    if submission.content.thumbnail_url
                    else None
                ),
                "score": submission.score,
                "flag_count": submission.flag_count,
                "created_at": submission.created_at.isoformat(),
                "updated_at": submission.updated_at.isoformat(),
            },
        )
        _insert_tags(connection, submission.id, submission.tags)
        _insert_content(connection, submission.id, submission.content)


def _insert_tags(
    connection: sqlite3.Connection, submission_id: str, tags: list[str]
) -> None:
    connection.executemany(
        """
        INSERT INTO submission_tags (submission_id, tag, position)
        VALUES (:submission_id, :tag, :position)
        """,
        [
            {"submission_id": submission_id, "tag": tag, "position": position}
            for position, tag in enumerate(tags)
        ],
    )


def _insert_content(
    connection: sqlite3.Connection,
    submission_id: str,
    content: ArticleContent | ImageContent | VideoContent | LinkContent,
) -> None:
    if isinstance(content, ArticleContent):
        connection.execute(
            """
            INSERT INTO submission_articles (
                submission_id,
                word_count,
                reading_time
            )
            VALUES (:submission_id, :word_count, :reading_time)
            """,
            {
                "submission_id": submission_id,
                "word_count": content.word_count,
                "reading_time": content.reading_time,
            },
        )
        return

    if isinstance(content, ImageContent):
        connection.execute(
            """
            INSERT INTO submission_images (submission_id, width, height)
            VALUES (:submission_id, :width, :height)
            """,
            {
                "submission_id": submission_id,
                "width": content.width,
                "height": content.height,
            },
        )
        return

    if isinstance(content, VideoContent):
        connection.execute(
            """
            INSERT INTO submission_videos (submission_id, duration, resolution)
            VALUES (:submission_id, :duration, :resolution)
            """,
            {
                "submission_id": submission_id,
                "duration": content.duration,
                "resolution": content.resolution,
            },
        )
        return

    connection.execute(
        """
        INSERT INTO submission_links (
            submission_id,
            domain,
            is_behind_paywall
        )
        VALUES (:submission_id, :domain, :is_behind_paywall)
        """,
        {
            "submission_id": submission_id,
            "domain": content.domain,
            "is_behind_paywall": int(content.is_behind_paywall),
        },
    )

