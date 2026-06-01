import sqlite3
from datetime import datetime

from app.domain.auth import AuthRole, AuthSession, AuthUser


class AuthRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get_user_by_email(self, email: str) -> AuthUser | None:
        row = self._connection.execute(
            """
            SELECT id, name, email, role, password_hash, created_at
            FROM auth_users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()
        return _to_user(row) if row is not None else None

    def create_session(
        self,
        *,
        session_id: str,
        user_id: str,
        refresh_token_hash: str,
        created_at: datetime,
        expires_at: datetime,
    ) -> AuthSession:
        self._connection.execute(
            """
            INSERT INTO auth_sessions (
                id, user_id, refresh_token_hash, created_at, expires_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                refresh_token_hash,
                created_at.isoformat(),
                expires_at.isoformat(),
            ),
        )
        session = self.get_active_session_by_refresh_token_hash(
            refresh_token_hash,
            now=created_at,
        )
        if session is None:
            raise RuntimeError("Created auth session could not be loaded")
        return session

    def get_active_session_by_refresh_token_hash(
        self,
        refresh_token_hash: str,
        *,
        now: datetime,
    ) -> AuthSession | None:
        row = self._connection.execute(
            """
            SELECT
                s.id AS session_id,
                s.refresh_token_hash,
                s.created_at AS session_created_at,
                s.expires_at,
                s.rotated_at,
                s.revoked_at,
                u.id AS user_id,
                u.name,
                u.email,
                u.role,
                u.password_hash,
                u.created_at AS user_created_at
            FROM auth_sessions AS s
            JOIN auth_users AS u ON u.id = s.user_id
            WHERE s.refresh_token_hash = ?
                AND s.revoked_at IS NULL
                AND s.expires_at > ?
            """,
            (refresh_token_hash, now.isoformat()),
        ).fetchone()
        return _to_session(row) if row is not None else None

    def rotate_session(
        self,
        *,
        session_id: str,
        refresh_token_hash: str,
        rotated_at: datetime,
        expires_at: datetime,
    ) -> AuthSession | None:
        self._connection.execute(
            """
            UPDATE auth_sessions
            SET refresh_token_hash = ?,
                rotated_at = ?,
                expires_at = ?
            WHERE id = ?
                AND revoked_at IS NULL
            """,
            (
                refresh_token_hash,
                rotated_at.isoformat(),
                expires_at.isoformat(),
                session_id,
            ),
        )
        return self.get_active_session_by_refresh_token_hash(
            refresh_token_hash,
            now=rotated_at,
        )

    def revoke_session(self, session_id: str, *, revoked_at: datetime) -> None:
        self._connection.execute(
            """
            UPDATE auth_sessions
            SET revoked_at = ?
            WHERE id = ?
            """,
            (revoked_at.isoformat(), session_id),
        )


def _to_user(row: sqlite3.Row) -> AuthUser:
    return AuthUser(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        role=AuthRole(row["role"]),
        password_hash=row["password_hash"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _to_session(row: sqlite3.Row) -> AuthSession:
    user = AuthUser(
        id=row["user_id"],
        name=row["name"],
        email=row["email"],
        role=AuthRole(row["role"]),
        password_hash=row["password_hash"],
        created_at=datetime.fromisoformat(row["user_created_at"]),
    )
    return AuthSession(
        id=row["session_id"],
        user=user,
        refresh_token_hash=row["refresh_token_hash"],
        created_at=datetime.fromisoformat(row["session_created_at"]),
        expires_at=datetime.fromisoformat(row["expires_at"]),
        rotated_at=_optional_datetime(row["rotated_at"]),
        revoked_at=_optional_datetime(row["revoked_at"]),
    )


def _optional_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value is not None else None
