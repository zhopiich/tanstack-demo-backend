import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class Settings:
    database_path: Path
    jwt_secret_key: str
    jwt_algorithm: str
    password_hash_iterations: int
    access_token_expires_seconds: int
    refresh_token_expires_seconds: int
    refresh_cookie_name: str
    refresh_cookie_path: str
    refresh_cookie_httponly: bool
    refresh_cookie_samesite: Literal["lax", "strict", "none"]
    refresh_cookie_secure: bool

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> Settings:
        source = os.environ if environ is None else environ
        refresh_cookie_samesite = source.get("REFRESH_COOKIE_SAMESITE", "lax")
        if refresh_cookie_samesite not in ("lax", "strict", "none"):
            raise ValueError(
                "REFRESH_COOKIE_SAMESITE must be one of: lax, strict, none"
            )

        return cls(
            database_path=Path(source.get("DATABASE_PATH", "data/app.db")),
            jwt_secret_key=source.get("JWT_SECRET_KEY", "dev-secret-key-change-me"),
            jwt_algorithm=source.get("JWT_ALGORITHM", "HS256"),
            password_hash_iterations=int(
                source.get("PASSWORD_HASH_ITERATIONS", "600000")
            ),
            access_token_expires_seconds=int(
                source.get("ACCESS_TOKEN_EXPIRES_SECONDS", "900")
            ),
            refresh_token_expires_seconds=int(
                source.get("REFRESH_TOKEN_EXPIRES_SECONDS", "604800")
            ),
            refresh_cookie_name=source.get("REFRESH_COOKIE_NAME", "refresh_token"),
            refresh_cookie_path=source.get("REFRESH_COOKIE_PATH", "/api/auth"),
            refresh_cookie_httponly=source.get(
                "REFRESH_COOKIE_HTTPONLY", "true"
            ).lower()
            == "true",
            refresh_cookie_samesite=refresh_cookie_samesite,
            refresh_cookie_secure=source.get("REFRESH_COOKIE_SECURE", "false").lower()
            == "true",
        )


def get_settings() -> Settings:
    return Settings.from_environment()
