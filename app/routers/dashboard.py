from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import require_current_user
from app.dependencies import get_dashboard_service
from app.schemas.auth import AuthUser
from app.schemas.dashboard import DashboardStatsResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(require_current_user)],
)


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    _: Annotated[AuthUser, Depends(require_current_user)],
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> DashboardStatsResponse:
    return DashboardStatsResponse(data=service.stats())
