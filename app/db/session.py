import sqlite3
from importlib.resources import files
from pathlib import Path

from app.db.seed import seed_database


def initialize_database(database_path: str | Path = ":memory:") -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(_read_schema())
    seed_database(connection)
    connection.commit()
    return connection


def _read_schema() -> str:
    return files("app.db").joinpath("schema.sql").read_text()
