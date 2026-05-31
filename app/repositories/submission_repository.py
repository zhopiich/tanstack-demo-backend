import sqlite3
from datetime import datetime

from app.domain import submission as domain


class SubmissionRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def list_submissions(self) -> list[domain.Submission]:
        rows = self._connection.execute(
            """
            SELECT
                submissions.id,
                submissions.title,
                submissions.status,
                submissions.content_type,
                submissions.content_url,
                submissions.thumbnail_url,
                submissions.score,
                submissions.flag_count,
                submissions.created_at,
                submissions.updated_at,
                submitters.id AS submitter_id,
                submitters.name AS submitter_name,
                submitters.email AS submitter_email,
                submitters.tier AS submitter_tier
            FROM submissions
            JOIN submitters ON submitters.id = submissions.submitter_id
            ORDER BY submissions.id
            """
        ).fetchall()

        return [self._to_submission(row) for row in rows]

    def get_submission(self, submission_id: str) -> domain.Submission | None:
        row = self._connection.execute(
            """
            SELECT
                submissions.id,
                submissions.title,
                submissions.status,
                submissions.content_type,
                submissions.content_url,
                submissions.thumbnail_url,
                submissions.score,
                submissions.flag_count,
                submissions.created_at,
                submissions.updated_at,
                submitters.id AS submitter_id,
                submitters.name AS submitter_name,
                submitters.email AS submitter_email,
                submitters.tier AS submitter_tier
            FROM submissions
            JOIN submitters ON submitters.id = submissions.submitter_id
            WHERE submissions.id = ?
            """,
            (submission_id,),
        ).fetchone()
        if row is None:
            return None
        return self._to_submission(row)

    def get_submitter_by_email(self, email: str) -> domain.Submitter | None:
        row = self._connection.execute(
            """
            SELECT id, name, email, tier
            FROM submitters
            WHERE email = ?
            """,
            (email,),
        ).fetchone()
        if row is None:
            return None
        return self._to_submitter(row)

    def _to_submitter(self, row: sqlite3.Row) -> domain.Submitter:
        return domain.Submitter(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            tier=domain.SubmitterTier(row["tier"]),
        )

    def _to_submission(self, row: sqlite3.Row) -> domain.Submission:
        submission_id = row["id"]
        return domain.Submission(
            id=submission_id,
            title=row["title"],
            status=domain.SubmissionStatus(row["status"]),
            submitter=domain.Submitter(
                id=row["submitter_id"],
                name=row["submitter_name"],
                email=row["submitter_email"],
                tier=domain.SubmitterTier(row["submitter_tier"]),
            ),
            content=self._get_content(
                submission_id=submission_id,
                content_type=domain.SubmissionType(row["content_type"]),
                url=row["content_url"],
                thumbnail_url=row["thumbnail_url"],
            ),
            tags=self._get_tags(submission_id),
            review=self._get_review(submission_id),
            score=row["score"],
            flag_count=row["flag_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _get_tags(self, submission_id: str) -> list[str]:
        rows = self._connection.execute(
            """
            SELECT tag
            FROM submission_tags
            WHERE submission_id = ?
            ORDER BY position
            """,
            (submission_id,),
        ).fetchall()
        return [row["tag"] for row in rows]

    def _get_review(self, submission_id: str) -> domain.Review | None:
        row = self._connection.execute(
            """
            SELECT reviewer_name, reviewer_email, verdict, reason, reviewed_at
            FROM reviews
            WHERE submission_id = ?
            """,
            (submission_id,),
        ).fetchone()
        if row is None:
            return None

        return domain.Review(
            reviewer=domain.Reviewer(
                name=row["reviewer_name"],
                email=row["reviewer_email"],
            ),
            verdict=domain.ReviewVerdict(row["verdict"]),
            reason=row["reason"],
            reviewed_at=datetime.fromisoformat(row["reviewed_at"]),
        )

    def _get_content(
        self,
        *,
        submission_id: str,
        content_type: domain.SubmissionType,
        url: str,
        thumbnail_url: str | None,
    ) -> domain.Content:
        if content_type is domain.SubmissionType.ARTICLE:
            row = self._connection.execute(
                """
                SELECT word_count, reading_time
                FROM submission_articles
                WHERE submission_id = ?
                """,
                (submission_id,),
            ).fetchone()
            return domain.ArticleContent(
                url=url,
                thumbnail_url=thumbnail_url,
                word_count=row["word_count"],
                reading_time=row["reading_time"],
            )

        if content_type is domain.SubmissionType.IMAGE:
            row = self._connection.execute(
                """
                SELECT width, height
                FROM submission_images
                WHERE submission_id = ?
                """,
                (submission_id,),
            ).fetchone()
            return domain.ImageContent(
                url=url,
                thumbnail_url=thumbnail_url,
                width=row["width"],
                height=row["height"],
            )

        if content_type is domain.SubmissionType.VIDEO:
            row = self._connection.execute(
                """
                SELECT duration, resolution
                FROM submission_videos
                WHERE submission_id = ?
                """,
                (submission_id,),
            ).fetchone()
            return domain.VideoContent(
                url=url,
                thumbnail_url=thumbnail_url,
                duration=row["duration"],
                resolution=domain.VideoResolution(row["resolution"]),
            )

        row = self._connection.execute(
            """
            SELECT domain, is_behind_paywall
            FROM submission_links
            WHERE submission_id = ?
            """,
            (submission_id,),
        ).fetchone()
        return domain.LinkContent(
            url=url,
            thumbnail_url=thumbnail_url,
            domain=row["domain"],
            is_behind_paywall=bool(row["is_behind_paywall"]),
        )
