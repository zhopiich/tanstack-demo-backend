import pytest

from app.core.config import Settings, get_settings


def test_settings_default_database_path() -> None:
    settings = Settings.from_environment({})

    assert settings.database_path.as_posix() == "data/app.db"


def test_settings_reads_database_path_from_environment() -> None:
    settings = Settings.from_environment({"DATABASE_PATH": "/tmp/content.db"})

    assert settings.database_path.as_posix() == "/tmp/content.db"


def test_get_settings_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_PATH", "/tmp/runtime.db")

    settings = get_settings()

    assert settings.database_path.as_posix() == "/tmp/runtime.db"


def test_settings_auth_defaults() -> None:
    settings = Settings.from_environment({})

    assert settings.jwt_secret_key == "dev-secret-key-change-me"
    assert settings.jwt_algorithm == "HS256"
    assert settings.password_hash_iterations == 600_000
    assert settings.access_token_expires_seconds == 900
    assert settings.refresh_token_expires_seconds == 604800
    assert settings.refresh_cookie_name == "refresh_token"
    assert settings.refresh_cookie_path == "/api/auth"
    assert settings.refresh_cookie_httponly is True
    assert settings.refresh_cookie_samesite == "lax"
    assert settings.refresh_cookie_secure is False
    assert settings.cors_allow_origins == []


def test_settings_reads_auth_environment() -> None:
    settings = Settings.from_environment(
        {
            "JWT_SECRET_KEY": "test-secret",
            "JWT_ALGORITHM": "HS256",
            "PASSWORD_HASH_ITERATIONS": "100",
            "ACCESS_TOKEN_EXPIRES_SECONDS": "60",
            "REFRESH_TOKEN_EXPIRES_SECONDS": "120",
            "REFRESH_COOKIE_NAME": "custom_refresh",
            "REFRESH_COOKIE_PATH": "/api/custom-auth",
            "REFRESH_COOKIE_HTTPONLY": "false",
            "REFRESH_COOKIE_SAMESITE": "strict",
            "REFRESH_COOKIE_SECURE": "true",
            "CORS_ALLOW_ORIGINS": (
                "http://localhost, https://tanstack-demo-frontend.example.com "
            ),
        }
    )

    assert settings.jwt_secret_key == "test-secret"
    assert settings.jwt_algorithm == "HS256"
    assert settings.password_hash_iterations == 100
    assert settings.access_token_expires_seconds == 60
    assert settings.refresh_token_expires_seconds == 120
    assert settings.refresh_cookie_name == "custom_refresh"
    assert settings.refresh_cookie_path == "/api/custom-auth"
    assert settings.refresh_cookie_httponly is False
    assert settings.refresh_cookie_samesite == "strict"
    assert settings.refresh_cookie_secure is True
    assert settings.cors_allow_origins == [
        "http://localhost",
        "https://tanstack-demo-frontend.example.com",
    ]


def test_settings_rejects_invalid_refresh_cookie_samesite() -> None:
    with pytest.raises(ValueError, match="REFRESH_COOKIE_SAMESITE"):
        Settings.from_environment({"REFRESH_COOKIE_SAMESITE": "invalid"})
