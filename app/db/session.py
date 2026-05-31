import sqlite3
from importlib.resources import files
from pathlib import Path

from app.db.seed import seed_database


def connect_database(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_runtime_database(database_path: str | Path) -> None:
    path = Path(database_path)
    if path.exists():
        return

    reset_database(path)


def reset_database(database_path: str | Path) -> None:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = connect_database(path)
    connection.executescript(_read_schema())
    seed_database(connection)
    connection.commit()
    connection.close()


def _read_schema() -> str:
    return files("app.db").joinpath("schema.sql").read_text()
