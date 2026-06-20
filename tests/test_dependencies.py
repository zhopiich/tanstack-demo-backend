import pytest

from app.core.config import Settings
from app.db.migrate import run_migrations
from app.db.seed import seed_database
from app.db.session import connect_database
from app.dependencies import get_database_connection


def _prepare_db(database_path) -> None:
    connection = connect_database(database_path)
    run_migrations(connection)
    seed_database(connection)
    connection.commit()
    connection.close()


def test_database_dependency_commits_successful_request(tmp_path) -> None:
    database_path = tmp_path / "content.db"
    _prepare_db(database_path)
    settings = Settings.from_environment({"DATABASE_PATH": str(database_path)})
    dependency = get_database_connection(settings)
    connection = next(dependency)

    connection.execute(
        """
        INSERT INTO submitters (id, name, email, tier)
        VALUES ('c999999999999999999999999', 'Temp User', 'temp@example.com', 'free')
        """
    )

    with pytest.raises(StopIteration):
        next(dependency)

    persisted_connection = connect_database(database_path)
    assert (
        persisted_connection.execute(
            "SELECT COUNT(*) AS count FROM submitters WHERE email = 'temp@example.com'"
        ).fetchone()["count"]
        == 1
    )
    persisted_connection.close()


def test_database_dependency_rolls_back_failed_request(tmp_path) -> None:
    database_path = tmp_path / "content.db"
    _prepare_db(database_path)
    settings = Settings.from_environment({"DATABASE_PATH": str(database_path)})
    dependency = get_database_connection(settings)
    connection = next(dependency)

    connection.execute(
        """
        INSERT INTO submitters (id, name, email, tier)
        VALUES ('c999999999999999999999999', 'Temp User', 'temp@example.com', 'free')
        """
    )

    with pytest.raises(RuntimeError):
        dependency.throw(RuntimeError("request failed"))

    persisted_connection = connect_database(database_path)
    assert (
        persisted_connection.execute(
            "SELECT COUNT(*) AS count FROM submitters WHERE email = 'temp@example.com'"
        ).fetchone()["count"]
        == 0
    )
    persisted_connection.close()


def test_database_dependency_closes_connection(tmp_path) -> None:
    database_path = tmp_path / "content.db"
    _prepare_db(database_path)
    settings = Settings.from_environment({"DATABASE_PATH": str(database_path)})
    dependency = get_database_connection(settings)
    connection = next(dependency)

    with pytest.raises(StopIteration):
        next(dependency)

    with pytest.raises(Exception, match="closed database"):
        connection.execute("SELECT 1")
