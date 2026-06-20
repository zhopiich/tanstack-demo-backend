from dataclasses import replace
from datetime import UTC, datetime
from math import ceil
from typing import Literal

from app.core.errors import ApiError
from app.domain import submission as domain
from app.mappers.submission_mapper import to_domain_content, to_submission_schema
from app.repositories.submission_repository import SubmissionRepository
from app.schemas.auth import AuthUser
from app.schemas.common import Pagination
from app.schemas.submission import (
    BatchDeleteBody,
    BatchReviewBody,
    DeletedCountResponse,
    SortOrder,
    Submission,
    SubmissionCreateBody,
    SubmissionListResponse,
    SubmissionStatus,
    SubmissionStatusUpdateBody,
    SubmissionType,
    SubmissionUpdateBody,
    SubmitterTier,
    UpdatedCountResponse,
)


class SubmissionService:
    def __init__(self, repository: SubmissionRepository) -> None:
        self._repository = repository

    def list_submissions(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: SubmissionStatus | None = None,
        type_: SubmissionType | None = None,
        tier: SubmitterTier | None = None,
        search: str | None = None,
        sort_by: Literal["createdAt", "score", "flagCount"] = "createdAt",
        sort_order: SortOrder = "desc",
    ) -> SubmissionListResponse:
        result = self._repository.find_submissions(
            status=domain.SubmissionStatus(status) if status else None,
            type_=domain.SubmissionType(type_) if type_ else None,
            tier=domain.SubmitterTier(tier) if tier else None,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=page_size,
            offset=(page - 1) * page_size,
        )

        return SubmissionListResponse(
            data=[to_submission_schema(submission) for submission in result.data],
            pagination=Pagination(
                page=page,
                pageSize=page_size,
                total=result.total,
                totalPages=ceil(result.total / page_size) if result.total else 0,
            ),
        )

    def get_submission(self, submission_id: str) -> Submission:
        return to_submission_schema(self._get_domain_submission(submission_id))

    def create_submission(self, body: SubmissionCreateBody) -> Submission:
        submitter = self._submitter_for_email(str(body.submitter_email))
        now = datetime.now(UTC)
        submission = domain.Submission(
            id=self._generate_submission_id(),
            title=body.title,
            status=domain.SubmissionStatus.PENDING,
            submitter=submitter,
            content=to_domain_content(body.content),
            tags=body.tags,
            review=None,
            score=0,
            flag_count=0,
            created_at=now,
            updated_at=now,
        )

        return to_submission_schema(self._repository.add_submission(submission))

    def update_submission(
        self,
        submission_id: str,
        body: SubmissionUpdateBody,
    ) -> Submission:
        submission = self._get_domain_submission(submission_id)
        update_data = body.model_dump(exclude_unset=True)

        updated = replace(
            submission,
            title=(
                body.title or submission.title
                if "title" in update_data
                else submission.title
            ),
            tags=(body.tags or [] if "tags" in update_data else submission.tags),
            content=(
                to_domain_content(body.content)
                if "content" in update_data and body.content is not None
                else submission.content
            ),
            updated_at=datetime.now(UTC),
        )

        saved = self._repository.update_submission(updated)
        if saved is None:
            raise ApiError(404, "submission_not_found", "Submission not found")

        return to_submission_schema(saved)

    def update_status(
        self,
        submission_id: str,
        body: SubmissionStatusUpdateBody,
    ) -> Submission:
        submission = self._get_domain_submission(submission_id)
        updated = replace(
            submission,
            status=domain.SubmissionStatus(body.status),
            updated_at=datetime.now(UTC),
        )
        saved = self._repository.update_submission(updated)
        if saved is None:
            raise ApiError(404, "submission_not_found", "Submission not found")

        return to_submission_schema(saved)

    def delete_submission(self, submission_id: str) -> None:
        self._get_domain_submission(submission_id)
        self._repository.delete_submission(submission_id)

    def batch_review(
        self,
        body: BatchReviewBody,
        reviewer: AuthUser,
    ) -> UpdatedCountResponse:
        submissions = self._submissions_by_ids(body.ids)
        now = datetime.now(UTC)

        for submission in submissions:
            self._repository.update_submission(
                replace(
                    submission,
                    status=domain.SubmissionStatus(body.verdict),
                    review=domain.Review(
                        reviewer=domain.Reviewer(
                            name=reviewer.name,
                            email=str(reviewer.email),
                        ),
                        verdict=domain.ReviewVerdict(body.verdict),
                        reason=body.reason,
                        reviewed_at=now,
                    ),
                    updated_at=now,
                )
            )

        return UpdatedCountResponse(updatedCount=len(submissions))

    def batch_delete(self, body: BatchDeleteBody) -> DeletedCountResponse:
        submissions = self._submissions_by_ids(body.ids)

        for submission in submissions:
            self._repository.delete_submission(submission.id)

        return DeletedCountResponse(deletedCount=len(submissions))

    def _get_domain_submission(self, submission_id: str) -> domain.Submission:
        submission = self._repository.get_submission(submission_id)
        if submission is None:
            raise ApiError(404, "submission_not_found", "Submission not found")

        return submission

    def _submitter_for_email(self, email: str) -> domain.Submitter:
        submitter = self._repository.get_submitter_by_email(email)
        if submitter is None:
            raise ApiError(404, "submitter_not_found", "Submitter not found")

        return submitter

    def _submissions_by_ids(self, ids: list[str]) -> list[domain.Submission]:
        unique_ids = list(dict.fromkeys(ids))
        submissions = self._repository.find_submissions_by_ids(unique_ids)

        if len(submissions) != len(unique_ids):
            raise ApiError(404, "submission_not_found", "Submission not found")

        return submissions

    def _generate_submission_id(self) -> str:
        existing_values = [
            int(submission.id[1:], 16)
            for submission in self._repository.list_submissions()
        ]
        return f"c{max(existing_values, default=0) + 1:024x}"
