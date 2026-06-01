from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AuthRole(StrEnum):
    ADMIN = "admin"
    REVIEWER = "reviewer"


@dataclass(frozen=True)
class AuthUser:
    id: str
    name: str
    email: str
    role: AuthRole
    password_hash: str
    created_at: datetime


@dataclass(frozen=True)
class AuthSession:
    id: str
    user: AuthUser
    refresh_token_hash: str
    created_at: datetime
    expires_at: datetime
    rotated_at: datetime | None
    revoked_at: datetime | None
