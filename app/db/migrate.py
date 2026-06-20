import hashlib
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

_MIGRATION_FILE_PATTERN = re.compile(r"^(\d+)_(.+)\.sql$")

_SCHEMA_MIGRATIONS_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    content_hash TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


@dataclass(frozen=True)
class MigrationFile:
    version: int
    filename: str
    path: Path
    script: str
    content_hash: str


def compute_hash(content: str) -> str:
    return f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"


def extract_table_names_from_sql(sql: str) -> list[str]:
    pattern = r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_][a-zA-Z0-9_]*)"
    return re.findall(pattern, sql, re.IGNORECASE)


def has_any_table(connection: sqlite3.Connection) -> bool:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return len(rows) > 0


def get_migration_files(migrations_dir: Path) -> list[MigrationFile]:
    if not migrations_dir.is_dir():
        raise FileNotFoundError(f"Migration directory not found: {migrations_dir}")

    result: list[MigrationFile] = []
    for path in sorted(migrations_dir.iterdir()):
        if not path.is_file() or path.suffix != ".sql":
            continue
        match = _MIGRATION_FILE_PATTERN.match(path.name)
        if not match:
            raise ValueError(
                f"Migration file '{path.name}' does not match expected pattern "
                f"(e.g., '001_description.sql')"
            )
        version = int(match.group(1))
        script = path.read_text()
        result.append(
            MigrationFile(
                version=version,
                filename=path.name,
                path=path,
                script=script,
                content_hash=compute_hash(script),
            )
        )
    result.sort(key=lambda m: m.version)
    return result
