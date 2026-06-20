import sqlite3
from datetime import UTC, datetime, timedelta

from app.core.tokens import hash_refresh_token
from app.db.migrate import run_migrations
from app.db.seed import seed_database
from app.db.session import connect_database
from app.domain.auth import AuthRole
from app.repositories.auth_repository import AuthRepository


def test_get_user_by_email_returns_domain_user(tmp_path) -> None:
    repository, connection = _repository(tmp_path)

    user = repository.get_user_by_email("reviewer@example.com")

    assert user is not None
    assert user.id == "c000000000000000000000001"
    assert user.name == "Reviewer User"
    assert user.email == "reviewer@example.com"
    assert user.role is AuthRole.REVIEWER
    assert user.password_hash.startswith("pbkdf2_sha256$")
    connection.close()


def test_get_user_by_email_returns_none_for_missing_user(tmp_path) -> None:
    repository, connection = _repository(tmp_path)

    assert repository.get_user_by_email("missing@example.com") is None
    connection.close()


def test_create_find_rotate_and_revoke_session(tmp_path) -> None:
    repository, connection = _repository(tmp_path)
    created_at = datetime(2026, 6, 1, 1, 0, tzinfo=UTC)
    expires_at = created_at + timedelta(days=7)

    session = repository.create_session(
        session_id="c400000000000000000000001",
        user_id="c000000000000000000000001",
        refresh_token_hash=hash_refresh_token("refresh-one"),
        created_at=created_at,
        expires_at=expires_at,
    )

    assert session.id == "c400000000000000000000001"
    active = repository.get_active_session_by_refresh_token_hash(
        hash_refresh_token("refresh-one"),
        now=created_at,
    )
    assert active is not None
    assert active.user.email == "reviewer@example.com"

    rotated_at = created_at + timedelta(minutes=5)
    rotated = repository.rotate_session(
        session_id=session.id,
        refresh_token_hash=hash_refresh_token("refresh-two"),
        rotated_at=rotated_at,
        expires_at=rotated_at + timedelta(days=7),
    )
    assert rotated is not None
    assert rotated.refresh_token_hash == hash_refresh_token("refresh-two")
    assert (
        repository.get_active_session_by_refresh_token_hash(
            hash_refresh_token("refresh-one"),
            now=rotated_at,
        )
        is None
    )

    repository.revoke_session(rotated.id, revoked_at=rotated_at)
    assert (
        repository.get_active_session_by_refresh_token_hash(
            hash_refresh_token("refresh-two"),
            now=rotated_at,
        )
        is None
    )
    connection.close()


def _repository(tmp_path) -> tuple[AuthRepository, sqlite3.Connection]:
    database_path = tmp_path / "content.db"
    connection = connect_database(database_path)
    run_migrations(connection)
    seed_database(connection)
    return AuthRepository(connection), connection
