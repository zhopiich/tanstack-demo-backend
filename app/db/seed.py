import sqlite3
from datetime import UTC, datetime
from typing import Any

from app.core.passwords import hash_password


def _seed_auth_user_rows() -> list[dict[str, Any]]:
    created_at = datetime(2026, 5, 29, 8, 0, tzinfo=UTC).isoformat()

    return [
        {
            "id": "a100000000000000000000001",
            "name": "Reviewer User",
            "email": "reviewer@example.com",
            "role": "reviewer",
            "password_hash": hash_password(
                "password123",
                salt=bytes.fromhex("00000000000000000000000000000001"),
            ),
            "created_at": created_at,
        },
        {
            "id": "a100000000000000000000002",
            "name": "Admin User",
            "email": "admin@example.com",
            "role": "admin",
            "password_hash": hash_password(
                "password123",
                salt=bytes.fromhex("00000000000000000000000000000002"),
            ),
            "created_at": created_at,
        },
    ]


def _seed_submission_rows() -> list[dict[str, Any]]:
    now = datetime(2026, 5, 29, 8, 0, tzinfo=UTC).isoformat()
    submitters = {
        "alex": {
            "id": "c100000000000000000000001",
            "name": "Alex Chen",
            "email": "alex@example.com",
            "tier": "pro",
        },
        "mina": {
            "id": "c100000000000000000000002",
            "name": "Mina Lin",
            "email": "mina@example.com",
            "tier": "verified",
        },
        "jordan": {
            "id": "c100000000000000000000003",
            "name": "Jordan Wu",
            "email": "jordan@example.com",
            "tier": "free",
        },
    }

    return [
        {
            "id": "c200000000000000000000001",
            "title": "Article moderation guide",
            "status": "pending",
            "submitter": submitters["alex"],
            "content": {
                "type": "article",
                "url": "https://example.com/articles/moderation-guide",
                "thumbnail_url": None,
                "word_count": 1800,
                "reading_time": 9,
            },
            "tags": ["editorial", "design"],
            "score": 82,
            "flag_count": 0,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "c200000000000000000000002",
            "title": "Launch image gallery",
            "status": "approved",
            "submitter": submitters["mina"],
            "content": {
                "type": "image",
                "url": "https://example.com/images/launch-gallery",
                "thumbnail_url": "https://example.com/images/launch-thumb",
                "width": 1600,
                "height": 900,
            },
            "tags": ["launch", "visual"],
            "score": 91,
            "flag_count": 1,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "c200000000000000000000003",
            "title": "Product walkthrough video",
            "status": "flagged",
            "submitter": submitters["alex"],
            "content": {
                "type": "video",
                "url": "https://example.com/videos/product-walkthrough",
                "thumbnail_url": "https://example.com/videos/product-thumb",
                "duration": 420,
                "resolution": "1080p",
            },
            "tags": ["product", "video"],
            "score": 64,
            "flag_count": 3,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "c200000000000000000000004",
            "title": "External research link",
            "status": "pending",
            "submitter": submitters["jordan"],
            "content": {
                "type": "link",
                "url": "https://example.com/research/content-trends",
                "thumbnail_url": None,
                "domain": "example.com",
                "is_behind_paywall": False,
            },
            "tags": ["research"],
            "score": 73,
            "flag_count": 0,
            "created_at": now,
            "updated_at": now,
        },
    ]


def seed_database(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT INTO auth_users (id, name, email, role, password_hash, created_at)
        VALUES (:id, :name, :email, :role, :password_hash, :created_at)
        """,
        _seed_auth_user_rows(),
    )

    submissions = _seed_submission_rows()
    submitters_by_id = {
        submission["submitter"]["id"]: submission["submitter"]
        for submission in submissions
    }

    connection.executemany(
        """
        INSERT INTO submitters (id, name, email, tier)
        VALUES (:id, :name, :email, :tier)
        """,
        [
            {
                "id": submitter["id"],
                "name": submitter["name"],
                "email": submitter["email"],
                "tier": submitter["tier"],
            }
            for submitter in submitters_by_id.values()
        ],
    )

    for submission in submissions:
        content = submission["content"]
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
                "id": submission["id"],
                "title": submission["title"],
                "status": submission["status"],
                "submitter_id": submission["submitter"]["id"],
                "content_type": content["type"],
                "content_url": content["url"],
                "thumbnail_url": content["thumbnail_url"],
                "score": submission["score"],
                "flag_count": submission["flag_count"],
                "created_at": submission["created_at"],
                "updated_at": submission["updated_at"],
            },
        )
        _insert_tags(connection, submission["id"], submission["tags"])
        _insert_content(connection, submission["id"], content)


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
    content: dict[str, Any],
) -> None:
    content_type = content["type"]

    if content_type == "article":
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
                "word_count": content["word_count"],
                "reading_time": content["reading_time"],
            },
        )
        return

    if content_type == "image":
        connection.execute(
            """
            INSERT INTO submission_images (submission_id, width, height)
            VALUES (:submission_id, :width, :height)
            """,
            {
                "submission_id": submission_id,
                "width": content["width"],
                "height": content["height"],
            },
        )
        return

    if content_type == "video":
        connection.execute(
            """
            INSERT INTO submission_videos (submission_id, duration, resolution)
            VALUES (:submission_id, :duration, :resolution)
            """,
            {
                "submission_id": submission_id,
                "duration": content["duration"],
                "resolution": content["resolution"],
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
            "domain": content["domain"],
            "is_behind_paywall": int(content["is_behind_paywall"]),
        },
    )
