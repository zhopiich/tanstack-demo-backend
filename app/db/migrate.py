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


def _get_migrations_dir() -> Path:
    from importlib.resources import files

    return Path(files("app.db.migrations").resolve())


def _record_applied(
    connection: sqlite3.Connection,
    migration: MigrationFile,
) -> None:
    connection.execute(
        "INSERT INTO schema_migrations (version, filename, content_hash) "
        "VALUES (?, ?, ?)",
        (migration.version, migration.filename, migration.content_hash),
    )


def _verify_applied_hashes(
    connection: sqlite3.Connection,
    available: list[MigrationFile],
) -> None:
    applied = {
        row["filename"]: row["content_hash"]
        for row in connection.execute(
            "SELECT filename, content_hash FROM schema_migrations ORDER BY version"
        ).fetchall()
    }
    for migration in available:
        if migration.filename in applied:
            if migration.content_hash != applied[migration.filename]:
                raise RuntimeError(
                    f"Migration '{migration.filename}' hash mismatch. "
                    f"File has been modified since it was applied."
                )


def _get_applied_versions(connection: sqlite3.Connection) -> set[int]:
    return {
        row["version"]
        for row in connection.execute(
            "SELECT version FROM schema_migrations"
        ).fetchall()
    }


def run_migrations(
    connection: sqlite3.Connection,
    *,
    up_to: int | None = None,
    migrations_dir: Path | None = None,
) -> tuple[int, int]:
    """Apply pending migrations.

    Returns (applied_count, stamped_count) for reporting.
    """
    if migrations_dir is None:
        migrations_dir = _get_migrations_dir()

    available = get_migration_files(migrations_dir)

    if not available:
        raise RuntimeError("No migration files found")

    if available[0].version != 1:
        raise RuntimeError("First migration file must be version 001")

    has_user_tables = has_any_table(connection)
    schema_migrations_exists = (
        connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='schema_migrations'"
        ).fetchone()
        is not None
    )

    applied_count = 0
    stamped_count = 0
    applied_versions: set[int] = set()

    if schema_migrations_exists:
        applied_versions = _get_applied_versions(connection)
        if applied_versions:
            _verify_applied_hashes(connection, available)

    if not applied_versions:
        connection.execute(_SCHEMA_MIGRATIONS_SQL)
        if has_user_tables:
            first = available[0]
            core_tables = extract_table_names_from_sql(first.script)
            for table in core_tables:
                count = connection.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                ).fetchone()[0]
                if count == 0:
                    raise RuntimeError(
                        f"Pre-migration database is missing required table "
                        f"'{table}' from baseline migration '{first.filename}'. "
                        f"Cannot safely adopt baseline."
                    )
            _record_applied(connection, first)
            stamped_count += 1
            applied_versions = {first.version}

    highest_applied = max(applied_versions) if applied_versions else 0

    if up_to is not None:
        pending = [
            m for m in available if m.version > highest_applied and m.version <= up_to
        ]
    else:
        pending = [m for m in available if m.version > highest_applied]

    for migration in pending:
        try:
            with connection:
                connection.executescript(migration.script)
            _record_applied(connection, migration)
            applied_count += 1
        except Exception as e:
            raise RuntimeError(f"Migration '{migration.filename}' failed: {e}") from e

    return applied_count, stamped_count
