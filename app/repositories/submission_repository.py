import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.domain import submission as domain

SortBy = Literal["createdAt", "score", "flagCount"]
SortOrder = Literal["asc", "desc"]


@dataclass(frozen=True)
class SubmissionListResult:
    data: list[domain.Submission]
    total: int


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

    def find_submissions(
        self,
        *,
        status: domain.SubmissionStatus | None = None,
        type_: domain.SubmissionType | None = None,
        tier: domain.SubmitterTier | None = None,
        search: str | None = None,
        sort_by: SortBy = "createdAt",
        sort_order: SortOrder = "desc",
        limit: int = 20,
        offset: int = 0,
    ) -> SubmissionListResult:
        where_sql, params = self._submission_filters(
            status=status,
            type_=type_,
            tier=tier,
            search=search,
        )
        total = self._count_submissions(where_sql, params)
        rows = self._find_submission_rows(
            where_sql=where_sql,
            params=params,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

        return SubmissionListResult(
            data=[self._to_submission(row) for row in rows],
            total=total,
        )

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

    def add_submission(self, submission: domain.Submission) -> domain.Submission:
        with self._connection:
            self._insert_submission(submission)

        created = self.get_submission(submission.id)
        if created is None:
            raise RuntimeError("Created submission could not be loaded")
        return created

    def update_submission(
        self, submission: domain.Submission
    ) -> domain.Submission | None:
        if self.get_submission(submission.id) is None:
            return None

        with self._connection:
            self._connection.execute(
                """
                UPDATE submissions
                SET
                    title = :title,
                    status = :status,
                    submitter_id = :submitter_id,
                    content_type = :content_type,
                    content_url = :content_url,
                    thumbnail_url = :thumbnail_url,
                    score = :score,
                    flag_count = :flag_count,
                    created_at = :created_at,
                    updated_at = :updated_at
                WHERE id = :id
                """,
                self._submission_row(submission),
            )
            self._replace_tags(submission)
            self._replace_content(submission)
            self._replace_review(submission)

        return self.get_submission(submission.id)

    def delete_submission(self, submission_id: str) -> bool:
        with self._connection:
            cursor = self._connection.execute(
                """
                DELETE FROM submissions
                WHERE id = ?
                """,
                (submission_id,),
            )

        return cursor.rowcount > 0

    def _submission_filters(
        self,
        *,
        status: domain.SubmissionStatus | None,
        type_: domain.SubmissionType | None,
        tier: domain.SubmitterTier | None,
        search: str | None,
    ) -> tuple[str, dict[str, object]]:
        clauses: list[str] = []
        params: dict[str, object] = {}

        if status is not None:
            clauses.append("submissions.status = :status")
            params["status"] = status.value

        if type_ is not None:
            clauses.append("submissions.content_type = :content_type")
            params["content_type"] = type_.value

        if tier is not None:
            clauses.append("submitters.tier = :tier")
            params["tier"] = tier.value

        query = search.strip().lower() if search else ""
        if query:
            clauses.append(
                """
                (
                    lower(submissions.title) LIKE :search
                    OR lower(submitters.name) LIKE :search
                    OR lower(submitters.email) LIKE :search
                    OR EXISTS (
                        SELECT 1
                        FROM submission_tags
                        WHERE submission_tags.submission_id = submissions.id
                        AND lower(submission_tags.tag) LIKE :search
                    )
                )
                """
            )
            params["search"] = f"%{query}%"

        if not clauses:
            return "", params

        return "WHERE " + " AND ".join(clauses), params

    def _count_submissions(
        self,
        where_sql: str,
        params: dict[str, object],
    ) -> int:
        row = self._connection.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM submissions
            JOIN submitters ON submitters.id = submissions.submitter_id
            {where_sql}
            """,
            params,
        ).fetchone()

        return row["total"]

    def _find_submission_rows(
        self,
        *,
        where_sql: str,
        params: dict[str, object],
        sort_by: SortBy,
        sort_order: SortOrder,
        limit: int,
        offset: int,
    ) -> list[sqlite3.Row]:
        query_params = params | {"limit": limit, "offset": offset}
        order_direction = "ASC" if sort_order == "asc" else "DESC"
        order_column = self._sort_column(sort_by)

        return self._connection.execute(
            f"""
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
            {where_sql}
            ORDER BY {order_column} {order_direction}, submissions.id ASC
            LIMIT :limit
            OFFSET :offset
            """,
            query_params,
        ).fetchall()

    def _sort_column(self, sort_by: SortBy) -> str:
        return {
            "createdAt": "submissions.created_at",
            "score": "submissions.score",
            "flagCount": "submissions.flag_count",
        }[sort_by]

    def _insert_submission(self, submission: domain.Submission) -> None:
        self._connection.execute(
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
            self._submission_row(submission),
        )
        self._insert_tags(submission)
        self._insert_content(submission)
        self._insert_review(submission)

    def _submission_row(self, submission: domain.Submission) -> dict[str, object]:
        return {
            "id": submission.id,
            "title": submission.title,
            "status": submission.status.value,
            "submitter_id": submission.submitter.id,
            "content_type": submission.content.type.value,
            "content_url": submission.content.url,
            "thumbnail_url": submission.content.thumbnail_url,
            "score": submission.score,
            "flag_count": submission.flag_count,
            "created_at": submission.created_at.isoformat(),
            "updated_at": submission.updated_at.isoformat(),
        }

    def _insert_tags(self, submission: domain.Submission) -> None:
        self._connection.executemany(
            """
            INSERT INTO submission_tags (submission_id, tag, position)
            VALUES (:submission_id, :tag, :position)
            """,
            [
                {
                    "submission_id": submission.id,
                    "tag": tag,
                    "position": position,
                }
                for position, tag in enumerate(submission.tags)
            ],
        )

    def _insert_content(self, submission: domain.Submission) -> None:
        content = submission.content
        if isinstance(content, domain.ArticleContent):
            self._connection.execute(
                """
                INSERT INTO submission_articles (
                    submission_id,
                    word_count,
                    reading_time
                )
                VALUES (:submission_id, :word_count, :reading_time)
                """,
                {
                    "submission_id": submission.id,
                    "word_count": content.word_count,
                    "reading_time": content.reading_time,
                },
            )
            return

        if isinstance(content, domain.ImageContent):
            self._connection.execute(
                """
                INSERT INTO submission_images (submission_id, width, height)
                VALUES (:submission_id, :width, :height)
                """,
                {
                    "submission_id": submission.id,
                    "width": content.width,
                    "height": content.height,
                },
            )
            return

        if isinstance(content, domain.VideoContent):
            self._connection.execute(
                """
                INSERT INTO submission_videos (
                    submission_id,
                    duration,
                    resolution
                )
                VALUES (:submission_id, :duration, :resolution)
                """,
                {
                    "submission_id": submission.id,
                    "duration": content.duration,
                    "resolution": content.resolution.value,
                },
            )
            return

        self._connection.execute(
            """
            INSERT INTO submission_links (
                submission_id,
                domain,
                is_behind_paywall
            )
            VALUES (:submission_id, :domain, :is_behind_paywall)
            """,
            {
                "submission_id": submission.id,
                "domain": content.domain,
                "is_behind_paywall": int(content.is_behind_paywall),
            },
        )

    def _replace_content(self, submission: domain.Submission) -> None:
        self._delete_content(submission.id)
        self._insert_content(submission)

    def _delete_content(self, submission_id: str) -> None:
        for table_name in (
            "submission_articles",
            "submission_images",
            "submission_videos",
            "submission_links",
        ):
            self._connection.execute(
                f"DELETE FROM {table_name} WHERE submission_id = ?",
                (submission_id,),
            )

    def _replace_tags(self, submission: domain.Submission) -> None:
        self._connection.execute(
            """
            DELETE FROM submission_tags
            WHERE submission_id = ?
            """,
            (submission.id,),
        )
        self._insert_tags(submission)

    def _insert_review(self, submission: domain.Submission) -> None:
        if submission.review is None:
            return

        self._connection.execute(
            """
            INSERT INTO reviews (
                submission_id,
                reviewer_name,
                reviewer_email,
                verdict,
                reason,
                reviewed_at
            )
            VALUES (
                :submission_id,
                :reviewer_name,
                :reviewer_email,
                :verdict,
                :reason,
                :reviewed_at
            )
            """,
            {
                "submission_id": submission.id,
                "reviewer_name": submission.review.reviewer.name,
                "reviewer_email": submission.review.reviewer.email,
                "verdict": submission.review.verdict.value,
                "reason": submission.review.reason,
                "reviewed_at": submission.review.reviewed_at.isoformat(),
            },
        )

    def _replace_review(self, submission: domain.Submission) -> None:
        self._connection.execute(
            """
            DELETE FROM reviews
            WHERE submission_id = ?
            """,
            (submission.id,),
        )
        self._insert_review(submission)

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

    def _tags_for_ids(self, ids: list[str]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {sid: [] for sid in ids}
        if not ids:
            return result
        placeholders = ",".join("?" * len(ids))
        rows = self._connection.execute(
            f"""
            SELECT submission_id, tag
            FROM submission_tags
            WHERE submission_id IN ({placeholders})
            ORDER BY submission_id, position
            """,
            ids,
        ).fetchall()
        for row in rows:
            result[row["submission_id"]].append(row["tag"])
        return result

    def _review_for_ids(
        self, ids: list[str]
    ) -> dict[str, domain.Review | None]:
        result: dict[str, domain.Review | None] = {sid: None for sid in ids}
        if not ids:
            return result
        placeholders = ",".join("?" * len(ids))
        rows = self._connection.execute(
            f"""
            SELECT submission_id, reviewer_name, reviewer_email,
                   verdict, reason, reviewed_at
            FROM reviews
            WHERE submission_id IN ({placeholders})
            """,
            ids,
        ).fetchall()
        for row in rows:
            result[row["submission_id"]] = domain.Review(
                reviewer=domain.Reviewer(
                    name=row["reviewer_name"],
                    email=row["reviewer_email"],
                ),
                verdict=domain.ReviewVerdict(row["verdict"]),
                reason=row["reason"],
                reviewed_at=datetime.fromisoformat(row["reviewed_at"]),
            )
        return result

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

    def _content_for_ids(
        self, rows: list[sqlite3.Row]
    ) -> dict[str, domain.Content]:
        result: dict[str, domain.Content] = {}
        if not rows:
            return result

        row_by_id: dict[str, sqlite3.Row] = {row["id"]: row for row in rows}

        by_type: dict[str, list[str]] = {}
        for row in rows:
            by_type.setdefault(row["content_type"], []).append(row["id"])

        if "article" in by_type:
            ids = by_type["article"]
            placeholders = ",".join("?" * len(ids))
            q_rows = self._connection.execute(
                f"""
                SELECT submission_id, word_count, reading_time
                FROM submission_articles
                WHERE submission_id IN ({placeholders})
                """,
                ids,
            ).fetchall()
            for r in q_rows:
                mr = row_by_id[r["submission_id"]]
                result[r["submission_id"]] = domain.ArticleContent(
                    url=mr["content_url"],
                    thumbnail_url=mr["thumbnail_url"],
                    word_count=r["word_count"],
                    reading_time=r["reading_time"],
                )

        if "image" in by_type:
            ids = by_type["image"]
            placeholders = ",".join("?" * len(ids))
            q_rows = self._connection.execute(
                f"""
                SELECT submission_id, width, height
                FROM submission_images
                WHERE submission_id IN ({placeholders})
                """,
                ids,
            ).fetchall()
            for r in q_rows:
                mr = row_by_id[r["submission_id"]]
                result[r["submission_id"]] = domain.ImageContent(
                    url=mr["content_url"],
                    thumbnail_url=mr["thumbnail_url"],
                    width=r["width"],
                    height=r["height"],
                )

        if "video" in by_type:
            ids = by_type["video"]
            placeholders = ",".join("?" * len(ids))
            q_rows = self._connection.execute(
                f"""
                SELECT submission_id, duration, resolution
                FROM submission_videos
                WHERE submission_id IN ({placeholders})
                """,
                ids,
            ).fetchall()
            for r in q_rows:
                mr = row_by_id[r["submission_id"]]
                result[r["submission_id"]] = domain.VideoContent(
                    url=mr["content_url"],
                    thumbnail_url=mr["thumbnail_url"],
                    duration=r["duration"],
                    resolution=domain.VideoResolution(r["resolution"]),
                )

        if "link" in by_type:
            ids = by_type["link"]
            placeholders = ",".join("?" * len(ids))
            q_rows = self._connection.execute(
                f"""
                SELECT submission_id, domain, is_behind_paywall
                FROM submission_links
                WHERE submission_id IN ({placeholders})
                """,
                ids,
            ).fetchall()
            for r in q_rows:
                mr = row_by_id[r["submission_id"]]
                result[r["submission_id"]] = domain.LinkContent(
                    url=mr["content_url"],
                    thumbnail_url=mr["thumbnail_url"],
                    domain=r["domain"],
                    is_behind_paywall=bool(r["is_behind_paywall"]),
                )

        return result
