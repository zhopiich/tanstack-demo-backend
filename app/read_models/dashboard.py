from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class DashboardSummaryReadModel:
    total_submissions: int
    pending_count: int
    approved_count: int
    rejected_count: int
    flagged_count: int


@dataclass(frozen=True)
class DashboardByTypeReadModel:
    type: Literal["article", "image", "video", "link"]
    count: int
    approval_rate: float


@dataclass(frozen=True)
class RecentActivityReadModel:
    submission_id: str
    title: str
    action: Literal["submitted", "approved", "rejected", "flagged"]
    actor_name: str
    occurred_at: datetime


@dataclass(frozen=True)
class TopSubmitterReadModel:
    submitter_id: str
    name: str
    tier: Literal["free", "pro", "verified"]
    submission_count: int
    approval_rate: float


@dataclass(frozen=True)
class DashboardStatsReadModel:
    summary: DashboardSummaryReadModel
    by_type: list[DashboardByTypeReadModel]
    recent_activity: list[RecentActivityReadModel]
    top_submitters: list[TopSubmitterReadModel]
