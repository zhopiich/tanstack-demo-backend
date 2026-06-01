import sqlite3
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.db.session import connect_database
from app.repositories.auth_repository import AuthRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.submission_repository import SubmissionRepository
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.services.submission_service import SubmissionService


def get_database_connection(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Generator[sqlite3.Connection]:
    connection = connect_database(settings.database_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_submission_repository(
    connection: Annotated[sqlite3.Connection, Depends(get_database_connection)],
) -> SubmissionRepository:
    return SubmissionRepository(connection)


def get_dashboard_repository(
    connection: Annotated[sqlite3.Connection, Depends(get_database_connection)],
) -> DashboardRepository:
    return DashboardRepository(connection)


def get_auth_repository(
    connection: Annotated[sqlite3.Connection, Depends(get_database_connection)],
) -> AuthRepository:
    return AuthRepository(connection)


def get_submission_service(
    repository: Annotated[SubmissionRepository, Depends(get_submission_repository)],
) -> SubmissionService:
    return SubmissionService(repository)


def get_dashboard_service(
    repository: Annotated[DashboardRepository, Depends(get_dashboard_repository)],
) -> DashboardService:
    return DashboardService(repository)


def get_auth_service(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(repository, settings)
