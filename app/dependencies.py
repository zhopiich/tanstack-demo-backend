from app.services.dashboard_service import DashboardService
from app.services.submission_service import SubmissionService
from app.stores.submission_store import InMemorySubmissionStore

submission_store = InMemorySubmissionStore()


def get_submission_store() -> InMemorySubmissionStore:
    return submission_store


def reset_submission_store() -> None:
    global submission_store
    submission_store = InMemorySubmissionStore()


def get_submission_service() -> SubmissionService:
    return SubmissionService(get_submission_store())


def get_dashboard_service() -> DashboardService:
    return DashboardService(get_submission_store())
