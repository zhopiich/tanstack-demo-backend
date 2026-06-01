from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.core.errors import ApiError
from app.core.security import require_current_user
from app.schemas.auth import AuthResponse, AuthUser, CurrentUserResponse, LoginBody
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@router.post("/login", response_model=AuthResponse)
def login(body: LoginBody) -> AuthResponse:
    result = auth_service.login(str(body.email), body.password)
    if result is None:
        raise ApiError(401, "invalid_credentials", "Invalid email or password")

    token, user = result
    return AuthResponse(accessToken=token, user=user, expiresIn=900)


@router.post("/logout", status_code=204)
def logout(_: Annotated[AuthUser, Depends(require_current_user)]) -> Response:
    return Response(status_code=204)


@router.get("/me", response_model=CurrentUserResponse)
def me(user: Annotated[AuthUser, Depends(require_current_user)]) -> CurrentUserResponse:
    return CurrentUserResponse(data=user)
