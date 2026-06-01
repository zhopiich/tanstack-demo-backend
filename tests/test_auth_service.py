from app.core.config import Settings
from app.core.tokens import decode_access_token
from app.db.session import connect_database, reset_database
from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import AuthService


def test_login_returns_access_token_user_and_refresh_token(tmp_path) -> None:
    service, connection, settings = _service(tmp_path)

    result = service.login("reviewer@example.com", "password123")

    assert result is not None
    assert result.user.email == "reviewer@example.com"
    assert result.user.role == "reviewer"
    assert result.access_token
    assert result.token_type == "Bearer"
    assert result.expires_in == 900
    assert result.refresh_token

    claims = decode_access_token(
        result.access_token,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    assert claims["sub"] == "c000000000000000000000001"
    assert claims["email"] == "reviewer@example.com"
    assert claims["role"] == "reviewer"
    assert (
        connection.execute("SELECT COUNT(*) AS count FROM auth_sessions").fetchone()[
            "count"
        ]
        == 1
    )
    connection.close()


def test_login_rejects_invalid_credentials(tmp_path) -> None:
    service, connection, _ = _service(tmp_path)

    assert service.login("reviewer@example.com", "wrongpass") is None
    assert service.login("missing@example.com", "password123") is None
    assert (
        connection.execute("SELECT COUNT(*) AS count FROM auth_sessions").fetchone()[
            "count"
        ]
        == 0
    )
    connection.close()


def test_refresh_rotates_refresh_token_and_keeps_one_session(tmp_path) -> None:
    service, connection, settings = _service(tmp_path)
    login = service.login("reviewer@example.com", "password123")
    assert login is not None

    refreshed = service.refresh(login.refresh_token)

    assert refreshed is not None
    assert refreshed.user.email == "reviewer@example.com"
    assert refreshed.refresh_token != login.refresh_token
    claims = decode_access_token(
        refreshed.access_token,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    assert claims["sub"] == "c000000000000000000000001"
    assert (
        connection.execute("SELECT COUNT(*) AS count FROM auth_sessions").fetchone()[
            "count"
        ]
        == 1
    )
    assert service.refresh(login.refresh_token) is None
    connection.close()


def test_refresh_rejects_invalid_token(tmp_path) -> None:
    service, connection, _ = _service(tmp_path)

    assert service.refresh("invalid-refresh-token") is None

    connection.close()


def test_logout_revokes_refresh_session(tmp_path) -> None:
    service, connection, _ = _service(tmp_path)
    login = service.login("reviewer@example.com", "password123")
    assert login is not None

    service.logout(login.refresh_token)

    assert service.refresh(login.refresh_token) is None
    revoked_count = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM auth_sessions
        WHERE revoked_at IS NOT NULL
        """
    ).fetchone()["count"]
    assert revoked_count == 1
    connection.close()


def test_logout_is_idempotent_for_missing_or_invalid_token(tmp_path) -> None:
    service, connection, _ = _service(tmp_path)

    service.logout(None)
    service.logout("invalid-refresh-token")

    assert (
        connection.execute("SELECT COUNT(*) AS count FROM auth_sessions").fetchone()[
            "count"
        ]
        == 0
    )
    connection.close()


def _service(tmp_path):
    database_path = tmp_path / "content.db"
    reset_database(database_path)
    connection = connect_database(database_path)
    settings = Settings.from_environment(
        {
            "DATABASE_PATH": database_path.as_posix(),
            "JWT_SECRET_KEY": "test-secret",
        }
    )
    return AuthService(AuthRepository(connection), settings), connection, settings
