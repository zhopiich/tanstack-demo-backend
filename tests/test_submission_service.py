from collections.abc import Iterator

import pytest

from app.core.errors import ApiError
from app.db.migrate import run_migrations
from app.db.seed import seed_database
from app.db.session import connect_database
from app.repositories.submission_repository import SubmissionRepository
from app.schemas.auth import AuthUser
from app.schemas.submission import BatchReviewBody, SubmissionCreateBody
from app.services.submission_service import SubmissionService


@pytest.fixture
def service(tmp_path) -> Iterator[SubmissionService]:
    database_path = tmp_path / "content.db"
    connection = connect_database(database_path)
    try:
        run_migrations(connection)
        seed_database(connection)
        yield SubmissionService(SubmissionRepository(connection))
    finally:
        connection.close()


def test_submission_service_creates_and_lists_with_sqlite_repository(
    service: SubmissionService,
) -> None:
    body = SubmissionCreateBody(
        title="SQLite service article",
        tags=["sqlite"],
        content={
            "type": "article",
            "url": "https://example.com/articles/sqlite-service",
            "thumbnailUrl": None,
            "wordCount": 900,
            "readingTime": 5,
        },
        submitterEmail="alex@example.com",
    )

    created = service.create_submission(body)
    listing = service.list_submissions(search="sqlite service")
    fetched = service.get_submission(created.id)

    assert created.title == "SQLite service article"
    assert created.status == "pending"
    assert created.submitter.email == "alex@example.com"
    assert created.content.type == "article"
    assert fetched.id == created.id
    assert listing.pagination.total == 1
    assert listing.data[0].id == created.id


def test_batch_review_is_all_or_nothing_with_sqlite_repository(
    service: SubmissionService,
) -> None:
    listing = service.list_submissions()
    existing = listing.data[0]

    try:
        service.batch_review(
            BatchReviewBody(
                ids=[existing.id, "c999999999999999999999999"],
                verdict="approved",
                reason="This content is ready for publishing",
            ),
            AuthUser(
                id="c300000000000000000000001",
                name="Demo Reviewer",
                email="reviewer@example.com",
                role="reviewer",
            ),
        )
    except ApiError as error:
        assert error.status_code == 404
        assert error.code == "submission_not_found"
    else:
        raise AssertionError("Expected missing submission to raise ApiError")

    unchanged = service.get_submission(existing.id)
    assert unchanged.status == existing.status
    assert unchanged.review == existing.review
