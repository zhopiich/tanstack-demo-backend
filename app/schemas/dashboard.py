from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.submission import SubmissionType, SubmitterTier


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class DashboardSummary(ApiModel):
    total_submissions: int = Field(alias="totalSubmissions", ge=0)
    pending_count: int = Field(alias="pendingCount", ge=0)
    approved_count: int = Field(alias="approvedCount", ge=0)
    rejected_count: int = Field(alias="rejectedCount", ge=0)
    flagged_count: int = Field(alias="flaggedCount", ge=0)


class DashboardByType(ApiModel):
    type: SubmissionType
    count: int = Field(ge=0)
    approval_rate: float = Field(alias="approvalRate", ge=0, le=1)


class RecentActivity(ApiModel):
    submission_id: str = Field(alias="submissionId", pattern=r"^c[a-z0-9]{24}$")
    title: str
    action: Literal["submitted", "approved", "rejected", "flagged"]
    actor_name: str = Field(alias="actorName")
    occurred_at: datetime = Field(alias="occurredAt")


class TopSubmitter(ApiModel):
    submitter_id: str = Field(alias="submitterId", pattern=r"^c[a-z0-9]{24}$")
    name: str
    tier: SubmitterTier
    submission_count: int = Field(alias="submissionCount", ge=0)
    approval_rate: float = Field(alias="approvalRate", ge=0, le=1)


class DashboardStats(ApiModel):
    summary: DashboardSummary
    by_type: list[DashboardByType] = Field(alias="byType")
    recent_activity: list[RecentActivity] = Field(alias="recentActivity")
    top_submitters: list[TopSubmitter] = Field(alias="topSubmitters")


class DashboardStatsResponse(ApiModel):
    data: DashboardStats
