import sqlite3

from app.db.session import initialize_database
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.submission_repository import SubmissionRepository
from app.services.dashboard_service import DashboardService
from app.services.submission_service import SubmissionService

database_connection = initialize_database()


def get_database_connection() -> sqlite3.Connection:
    return database_connection


def reset_database() -> None:
    global database_connection
    database_connection.close()
    database_connection = initialize_database()


def get_submission_repository() -> SubmissionRepository:
    return SubmissionRepository(get_database_connection())


def get_dashboard_repository() -> DashboardRepository:
    return DashboardRepository(get_database_connection())


def get_submission_service() -> SubmissionService:
    return SubmissionService(get_submission_repository())


def get_dashboard_service() -> DashboardService:
    return DashboardService(get_dashboard_repository())
