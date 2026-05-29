from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from app.schemas.common import Pagination


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


SubmissionStatus = Literal["pending", "approved", "rejected", "flagged"]
SubmissionType = Literal["article", "image", "video", "link"]
SubmitterTier = Literal["free", "pro", "verified"]
VideoResolution = Literal["480p", "720p", "1080p", "4k"]
ReviewVerdict = Literal["approved", "rejected"]
SortOrder = Literal["asc", "desc"]


class Submitter(ApiModel):
    id: str = Field(pattern=r"^c[a-z0-9]{24}$")
    name: str
    email: EmailStr
    tier: SubmitterTier


class BaseContent(ApiModel):
    url: HttpUrl
    thumbnail_url: HttpUrl | None = Field(alias="thumbnailUrl")


class ArticleContent(BaseContent):
    type: Literal["article"]
    word_count: int = Field(alias="wordCount", ge=1)
    reading_time: int = Field(alias="readingTime", ge=1)


class VideoContent(BaseContent):
    type: Literal["video"]
    duration: int = Field(ge=1)
    resolution: VideoResolution


class ImageContent(BaseContent):
    type: Literal["image"]
    width: int = Field(ge=1)
    height: int = Field(ge=1)


class LinkContent(BaseContent):
    type: Literal["link"]
    domain: str
    is_behind_paywall: bool = Field(alias="isBehindPaywall")


Content = Annotated[
    ArticleContent | VideoContent | ImageContent | LinkContent,
    Field(discriminator="type"),
]


class Reviewer(ApiModel):
    name: str
    email: EmailStr


class Review(ApiModel):
    reviewer: Reviewer
    verdict: ReviewVerdict
    reason: str = Field(min_length=10)
    reviewed_at: datetime = Field(alias="reviewedAt")


class Submission(ApiModel):
    id: str = Field(pattern=r"^c[a-z0-9]{24}$")
    title: str = Field(min_length=1, max_length=100)
    status: SubmissionStatus
    submitter: Submitter
    content: Content
    tags: list[str] = Field(max_length=5)
    review: Review | None
    score: int = Field(ge=0, le=100)
    flag_count: int = Field(alias="flagCount", ge=0)
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class SubmissionResponse(ApiModel):
    data: Submission


class SubmissionListResponse(ApiModel):
    data: list[Submission]
    pagination: Pagination


class SubmissionCreateBody(ApiModel):
    title: str = Field(min_length=1, max_length=100)
    tags: list[str] = Field(max_length=5)
    content: Content
    submitter_email: EmailStr | None = Field(default=None, alias="submitterEmail")


class SubmissionUpdateBody(ApiModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    tags: list[str] | None = Field(default=None, max_length=5)
    content: Content | None = None


class SubmissionStatusUpdateBody(ApiModel):
    status: Literal["pending", "flagged"]


class BatchReviewBody(ApiModel):
    ids: list[str] = Field(min_length=1)
    verdict: ReviewVerdict
    reason: str = Field(min_length=10)


class BatchDeleteBody(ApiModel):
    ids: list[str] = Field(min_length=1)


class UpdatedCountResponse(ApiModel):
    updated_count: int = Field(alias="updatedCount")


class DeletedCountResponse(ApiModel):
    deleted_count: int = Field(alias="deletedCount")
