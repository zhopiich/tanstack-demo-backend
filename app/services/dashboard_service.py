from app.mappers.dashboard_mapper import to_dashboard_stats_schema
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardStats


class DashboardService:
    def __init__(self, repository: DashboardRepository) -> None:
        self._repository = repository

    def stats(self) -> DashboardStats:
        return to_dashboard_stats_schema(self._repository.stats())
