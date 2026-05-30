from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from app.core.security import require_current_user
from app.dependencies import get_submission_service
from app.schemas.auth import AuthUser
from app.schemas.submission import (
    BatchDeleteBody,
    BatchReviewBody,
    DeletedCountResponse,
    SortOrder,
    SubmissionCreateBody,
    SubmissionListResponse,
    SubmissionResponse,
    SubmissionStatus,
    SubmissionStatusUpdateBody,
    SubmissionType,
    SubmissionUpdateBody,
    SubmitterTier,
    UpdatedCountResponse,
)
from app.services.submission_service import SubmissionService

router = APIRouter(
    prefix="/submissions",
    tags=["submissions"],
    dependencies=[Depends(require_current_user)],
)


@router.get("", response_model=SubmissionListResponse)
def list_submissions(
    _: Annotated[AuthUser, Depends(require_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
    status: SubmissionStatus | None = None,
    type_: Annotated[SubmissionType | None, Query(alias="type")] = None,
    tier: SubmitterTier | None = None,
    search: str | None = None,
    sort_by: Annotated[
        Literal["createdAt", "score", "flagCount"],
        Query(alias="sortBy"),
    ] = "createdAt",
    sort_order: Annotated[SortOrder, Query(alias="sortOrder")] = "desc",
) -> SubmissionListResponse:
    return service.list_submissions(
        page=page,
        page_size=page_size,
        status=status,
        type_=type_,
        tier=tier,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post("", status_code=201, response_model=SubmissionResponse)
def create_submission(
    body: SubmissionCreateBody,
    _: Annotated[AuthUser, Depends(require_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionResponse:
    return SubmissionResponse(data=service.create_submission(body))


@router.post("/batch-review", response_model=UpdatedCountResponse)
def batch_review_submissions(
    body: BatchReviewBody,
    current_user: Annotated[AuthUser, Depends(require_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> UpdatedCountResponse:
    return service.batch_review(body, current_user)


@router.post("/batch-delete", response_model=DeletedCountResponse)
def batch_delete_submissions(
    body: BatchDeleteBody,
    _: Annotated[AuthUser, Depends(require_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> DeletedCountResponse:
    return service.batch_delete(body)


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
