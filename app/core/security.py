from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.tokens import InvalidTokenError, decode_access_token
from app.schemas.auth import AuthUser

bearer_scheme = HTTPBearer(auto_error=False)


def require_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError(401, "unauthorized", "Missing bearer token")

    try:
        claims = decode_access_token(
            credentials.credentials,
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        return AuthUser(
            id=str(claims["sub"]),
            name=str(claims["name"]),
            email=str(claims["email"]),
            role=claims["role"],
        )
    except InvalidTokenError, KeyError, ValueError:
        raise ApiError(401, "unauthorized", "Invalid bearer token") from None


def require_admin(
    current_user: Annotated[AuthUser, Depends(require_current_user)],
) -> AuthUser:
    if current_user.role != "admin":
        raise ApiError(403, "forbidden", "Insufficient permissions")
    return current_user
