from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import require_current_user
from app.schemas.auth import AuthUser
from app.schemas.submission import SubmissionListResponse, SubmissionResponse
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


@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: str,
    _: Annotated[AuthUser, Depends(require_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionResponse:
    return SubmissionResponse(data=service.get_submission(submission_id))
