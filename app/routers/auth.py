from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.security import require_current_user
from app.dependencies import get_auth_service
from app.schemas.auth import AuthResponse, AuthUser, CurrentUserResponse, LoginBody
from app.services.auth_service import AuthResult, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
def login(
    body: LoginBody,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    result = service.login(str(body.email), body.password)
    if result is None:
        raise ApiError(401, "invalid_credentials", "Invalid email or password")

    _set_refresh_cookie(
        response,
        refresh_token=result.refresh_token,
        settings=settings,
    )
    return _auth_response(result)


@router.post("/refresh", response_model=AuthResponse)
def refresh(
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> AuthResponse:
    if refresh_token is None:
        raise ApiError(401, "unauthorized", "Invalid refresh token")

    result = service.refresh(refresh_token)
    if result is None:
        raise ApiError(401, "unauthorized", "Invalid refresh token")

    _set_refresh_cookie(
        response,
        refresh_token=result.refresh_token,
        settings=settings,
    )
    return _auth_response(result)


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    service.logout(refresh_token)
    _clear_refresh_cookie(response, settings=settings)
    return Response(status_code=204, headers=dict(response.headers))


@router.get("/me", response_model=CurrentUserResponse)
def me(user: Annotated[AuthUser, Depends(require_current_user)]) -> CurrentUserResponse:
    return CurrentUserResponse(data=user)


def _auth_response(result: AuthResult) -> AuthResponse:
    return AuthResponse(
        user=result.user,
        accessToken=result.access_token,
        tokenType="Bearer",
        expiresIn=result.expires_in,
    )


def _set_refresh_cookie(
    response: Response,
    *,
    refresh_token: str,
    settings: Settings,
) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        max_age=settings.refresh_token_expires_seconds,
        httponly=settings.refresh_cookie_httponly,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=settings.refresh_cookie_path,
    )


def _clear_refresh_cookie(response: Response, *, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=settings.refresh_cookie_path,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )
