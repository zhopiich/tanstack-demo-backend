from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import ApiError
from app.schemas.auth import AuthUser
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)
auth_service = AuthService()


def require_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError(401, "unauthorized", "Missing bearer token")

    user = auth_service.get_user_for_token(credentials.credentials)
    if user is None:
        raise ApiError(401, "unauthorized", "Invalid bearer token")

    return user
