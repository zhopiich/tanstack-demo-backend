from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SubmissionStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class SubmissionType(StrEnum):
    ARTICLE = "article"
    IMAGE = "image"
    VIDEO = "video"
    LINK = "link"


class SubmitterTier(StrEnum):
    FREE = "free"
    PRO = "pro"
    VERIFIED = "verified"


class VideoResolution(StrEnum):
    P480 = "480p"
    P720 = "720p"
    P1080 = "1080p"
    K4 = "4k"


class ReviewVerdict(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Submitter:
    id: str
    name: str
    email: str
    tier: SubmitterTier


@dataclass(frozen=True)
class BaseContent:
    url: str
    thumbnail_url: str | None


@dataclass(frozen=True)
class ArticleContent(BaseContent):
    word_count: int
    reading_time: int

    @property
    def type(self) -> SubmissionType:
        return SubmissionType.ARTICLE


@dataclass(frozen=True)
class ImageContent(BaseContent):
    width: int
    height: int

    @property
    def type(self) -> SubmissionType:
        return SubmissionType.IMAGE


@dataclass(frozen=True)
class VideoContent(BaseContent):
    duration: int
    resolution: VideoResolution

    @property
    def type(self) -> SubmissionType:
        return SubmissionType.VIDEO


@dataclass(frozen=True)
class LinkContent(BaseContent):
    domain: str
    is_behind_paywall: bool

    @property
    def type(self) -> SubmissionType:
        return SubmissionType.LINK


Content = ArticleContent | ImageContent | VideoContent | LinkContent


@dataclass(frozen=True)
class Reviewer:
    name: str
    email: str


@dataclass(frozen=True)
class Review:
    reviewer: Reviewer
    verdict: ReviewVerdict
    reason: str
    reviewed_at: datetime


@dataclass(frozen=True)
class Submission:
    id: str
    title: str
    status: SubmissionStatus
    submitter: Submitter
    content: Content
    tags: list[str]
    review: Review | None
    score: int
    flag_count: int
    created_at: datetime
    updated_at: datetime
