from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.config import Settings
from app.core.passwords import verify_password
from app.core.tokens import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.domain.auth import AuthUser as DomainAuthUser
from app.mappers.auth_mapper import to_auth_user_schema
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import AuthUser


@dataclass(frozen=True)
class AuthResult:
    user: AuthUser
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str


class AuthService:
    def __init__(self, repository: AuthRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    def login(self, email: str, password: str) -> AuthResult | None:
        user = self._repository.get_user_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            return None

        return self._issue_auth_result(user)

    def refresh(self, refresh_token: str) -> AuthResult | None:
        now = datetime.now(UTC)
        session = self._repository.get_active_session_by_refresh_token_hash(
            hash_refresh_token(refresh_token),
            now=now,
        )
        if session is None:
            return None

        new_refresh_token = generate_refresh_token()
        rotated_session = self._repository.rotate_session(
            session_id=session.id,
            refresh_token_hash=hash_refresh_token(new_refresh_token),
            rotated_at=now,
            expires_at=now
            + timedelta(seconds=self._settings.refresh_token_expires_seconds),
        )
        if rotated_session is None:
            return None

        return self._auth_result(
            user=rotated_session.user,
            refresh_token=new_refresh_token,
        )

    def logout(self, refresh_token: str | None) -> None:
        if refresh_token is None:
            return

        now = datetime.now(UTC)
        session = self._repository.get_active_session_by_refresh_token_hash(
            hash_refresh_token(refresh_token),
            now=now,
        )
        if session is None:
            return

        self._repository.revoke_session(session.id, revoked_at=now)

    def _issue_auth_result(self, user: DomainAuthUser) -> AuthResult:
        refresh_token = generate_refresh_token()
        now = datetime.now(UTC)
        self._repository.create_session(
            session_id=_content_id(),
            user_id=user.id,
            refresh_token_hash=hash_refresh_token(refresh_token),
            created_at=now,
            expires_at=now
            + timedelta(seconds=self._settings.refresh_token_expires_seconds),
        )
        return self._auth_result(user=user, refresh_token=refresh_token)

    def _auth_result(
        self,
        *,
        user: DomainAuthUser,
        refresh_token: str,
    ) -> AuthResult:
        return AuthResult(
            user=to_auth_user_schema(user),
            access_token=create_access_token(
                claims={
                    "sub": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role.value,
                },
                secret_key=self._settings.jwt_secret_key,
                algorithm=self._settings.jwt_algorithm,
                expires_in_seconds=self._settings.access_token_expires_seconds,
            ),
            token_type="Bearer",
            expires_in=self._settings.access_token_expires_seconds,
            refresh_token=refresh_token,
        )


def _content_id() -> str:
    return "c" + uuid4().hex[:24]
