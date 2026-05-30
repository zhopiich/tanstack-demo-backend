from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.core.security import require_current_user
from app.schemas.auth import AuthUser
from app.schemas.submission import (
    SubmissionCreateBody,
    SubmissionListResponse,
    SubmissionResponse,
    SubmissionStatusUpdateBody,
    SubmissionUpdateBody,
)
from app.services.submission_service import SubmissionService

router = APIRouter(
    prefix="/submissions",
    tags=["submissions"],
    dependencies=[Depends(require_current_user)],
)

submission_service = SubmissionService()


def get_submission_service() -> SubmissionService:
    return submission_service


@router.get("", response_model=SubmissionListResponse)
def list_submissions(
    _: Annotated[AuthUser, Depends(require_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionListResponse:
    return service.list_submissions()


@router.post("", status_code=201, response_model=SubmissionResponse)
def create_submission(
    body: SubmissionCreateBody,
    _: Annotated[AuthUser, Depends(require_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionResponse:
    return SubmissionResponse(data=service.create_submission(body))


@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: str,
    _: Annotated[AuthUser, Depends(require_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionResponse:
    return SubmissionResponse(data=service.get_submission(submission_id))


@router.patch("/{submission_id}", response_model=SubmissionResponse)
def update_submission(
    submission_id: str,
    body: SubmissionUpdateBody,
    _: Annotated[AuthUser, Depends(require_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionResponse:
    return SubmissionResponse(data=service.update_submission(submission_id, body))


@router.delete("/{submission_id}", status_code=204)
def delete_submission(
    submission_id: str,
    _: Annotated[AuthUser, Depends(require_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> Response:
    service.delete_submission(submission_id)
    return Response(status_code=204)


@router.patch("/{submission_id}/status", response_model=SubmissionResponse)
def update_submission_status(
    submission_id: str,
    body: SubmissionStatusUpdateBody,
    _: Annotated[AuthUser, Depends(require_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionResponse:
    return SubmissionResponse(data=service.update_status(submission_id, body))
