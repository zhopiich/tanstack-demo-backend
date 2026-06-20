import os
import sqlite3
from pathlib import Path

from app.db.migrate import run_migrations
from app.db.seed import seed_database


def connect_database(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_runtime_database(database_path: str | Path) -> None:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = connect_database(path)
    try:
        run_migrations(connection)
        env = os.getenv("ENV", "development")
        if env in ("development", "test"):
            seed_database(connection)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
