import hashlib
import sqlite3
from pathlib import Path

import pytest

from app.db.migrate import (
    compute_hash,
    extract_table_names_from_sql,
    get_migration_files,
    has_any_table,
    run_migrations,
)


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def test_compute_hash_returns_sha256_with_prefix() -> None:
    result = compute_hash("CREATE TABLE foo (id INT);")
    expected = "sha256:" + hashlib.sha256(b"CREATE TABLE foo (id INT);").hexdigest()
    assert result == expected


def test_compute_hash_is_deterministic() -> None:
    content = "SELECT 1;"
    assert compute_hash(content) == compute_hash(content)


def test_extract_table_names_from_sql_simple() -> None:
    sql = "CREATE TABLE users (id INT);"
    assert extract_table_names_from_sql(sql) == ["users"]


def test_extract_table_names_from_sql_multiple() -> None:
    sql = """
    CREATE TABLE users (id INT);
    CREATE TABLE posts (id INT);
    """
    assert extract_table_names_from_sql(sql) == ["users", "posts"]


def test_extract_table_names_from_sql_with_if_not_exists() -> None:
    sql = "CREATE TABLE IF NOT EXISTS users (id INT);"
    assert extract_table_names_from_sql(sql) == ["users"]


def test_extract_table_names_from_sql_empty() -> None:
    assert extract_table_names_from_sql("-- comment\nSELECT 1;") == []


def test_has_any_table_returns_false_for_empty_db(tmp_path) -> None:
    db = tmp_path / "empty.db"
    conn = _connect(db)
    assert has_any_table(conn) is False
    conn.close()


def test_has_any_table_returns_true_when_table_exists(tmp_path) -> None:
    db = tmp_path / "test.db"
    conn = _connect(db)
    conn.execute("CREATE TABLE users (id INT)")
    assert has_any_table(conn) is True
    conn.close()


def test_get_migration_files_returns_sorted_migrations(tmp_path) -> None:
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "002_second.sql").write_text("")
    (migrations_dir / "001_first.sql").write_text("")
    (migrations_dir / "010_tenth.sql").write_text("")

    result = get_migration_files(migrations_dir)

    assert [m.version for m in result] == [1, 2, 10]
    assert [m.filename for m in result] == [
        "001_first.sql",
        "002_second.sql",
        "010_tenth.sql",
    ]


def test_get_migration_files_raises_on_bad_filename(tmp_path) -> None:
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "bad_name.sql").write_text("")

    with pytest.raises(ValueError, match="does not match expected pattern"):
        get_migration_files(migrations_dir)


def test_get_migration_files_computes_hash(tmp_path) -> None:
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "001_init.sql").write_text("CREATE TABLE t (id INT);")

    result = get_migration_files(migrations_dir)

    assert result[0].content_hash == compute_hash("CREATE TABLE t (id INT);")


def test_run_migrations_on_fresh_db(tmp_path) -> None:
    db = tmp_path / "fresh.db"
    conn = _connect(db)
    migrations_dir = _prepare_migrations_dir(
        tmp_path,
        "001_initial.sql",
        """
        CREATE TABLE users (id INT PRIMARY KEY, name TEXT);
    """,
    )

    run_migrations(conn, migrations_dir=migrations_dir)

    tables = {
        r["name"]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "schema_migrations" in tables
    assert "users" in tables
    assert conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1
    conn.close()


def test_run_migrations_applies_multiple_migrations_in_order(tmp_path) -> None:
    db = tmp_path / "test.db"
    conn = _connect(db)
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "001_users.sql").write_text(
        "CREATE TABLE users (id INT PRIMARY KEY, name TEXT);"
    )
    (migrations_dir / "002_posts.sql").write_text(
        "CREATE TABLE posts (id INT PRIMARY KEY, user_id INT, title TEXT);"
    )

    run_migrations(conn, migrations_dir=migrations_dir)

    tables = {
        r["name"]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "users" in tables
    assert "posts" in tables
    assert conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 2
    conn.close()


def test_run_migrations_is_idempotent_on_already_migrated_db(tmp_path) -> None:
    db = tmp_path / "test.db"
    conn = _connect(db)
    migrations_dir = _prepare_migrations_dir(
        tmp_path, "001_users.sql", "CREATE TABLE users (id INT PRIMARY KEY, name TEXT);"
    )

    run_migrations(conn, migrations_dir=migrations_dir)
    run_migrations(conn, migrations_dir=migrations_dir)

    assert conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1
    conn.close()


def test_run_migrations_fails_fast_on_hash_mismatch(tmp_path) -> None:
    db = tmp_path / "test.db"
    conn = _connect(db)
    migrations_dir = _prepare_migrations_dir(
        tmp_path, "001_users.sql", "CREATE TABLE users (id INT PRIMARY KEY, name TEXT);"
    )

    run_migrations(conn, migrations_dir=migrations_dir)

    (migrations_dir / "001_users.sql").write_text(
        "CREATE TABLE users (id INT PRIMARY KEY, name TEXT, email TEXT);"
    )

    with pytest.raises(RuntimeError, match="hash mismatch"):
        run_migrations(conn, migrations_dir=migrations_dir)
    conn.close()


def test_run_migrations_stamps_baseline_for_existing_db(tmp_path) -> None:
    db = tmp_path / "existing.db"
    conn = _connect(db)
    conn.execute("CREATE TABLE users (id INT PRIMARY KEY, name TEXT);")
    conn.commit()

    migrations_dir = _prepare_migrations_dir(
        tmp_path, "001_users.sql", "CREATE TABLE users (id INT PRIMARY KEY, name TEXT);"
    )

    run_migrations(conn, migrations_dir=migrations_dir)

    assert conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1
    row = conn.execute("SELECT version, filename FROM schema_migrations").fetchone()
    assert row["version"] == 1
    assert row["filename"] == "001_users.sql"
    conn.close()


def test_run_migrations_fails_on_baseline_with_missing_core_table(tmp_path) -> None:
    db = tmp_path / "partial.db"
    conn = _connect(db)
    conn.execute("CREATE TABLE users (id INT PRIMARY KEY, name TEXT);")
    conn.commit()

    migrations_dir = _prepare_migrations_dir(
        tmp_path,
        "001_users.sql",
        "CREATE TABLE users (id INT PRIMARY KEY, name TEXT);\n"
        "CREATE TABLE posts (id INT PRIMARY KEY, title TEXT);",
    )

    with pytest.raises(RuntimeError, match="missing required table"):
        run_migrations(conn, migrations_dir=migrations_dir)
    conn.close()


def test_run_migrations_rolls_back_on_sql_error(tmp_path) -> None:
    db = tmp_path / "failing.db"
    conn = _connect(db)
    migrations_dir = _prepare_migrations_dir(
        tmp_path,
        "001_users.sql",
        "CREATE TABLE users (id INT PRIMARY KEY, name TEXT);\nINVALID SQL STATEMENT;",
    )

    with pytest.raises(RuntimeError, match="failed"):
        run_migrations(conn, migrations_dir=migrations_dir)

    assert conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 0
    conn.close()


def test_run_migrations_respects_up_to(tmp_path) -> None:
    db = tmp_path / "test.db"
    conn = _connect(db)
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "001_users.sql").write_text(
        "CREATE TABLE users (id INT PRIMARY KEY, name TEXT);"
    )
    (migrations_dir / "002_posts.sql").write_text(
        "CREATE TABLE posts (id INT PRIMARY KEY, user_id INT);"
    )

    run_migrations(conn, migrations_dir=migrations_dir, up_to=1)

    tables = {
        r["name"]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "users" in tables
    assert "posts" not in tables
    assert conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1
    conn.close()


def test_run_migrations_returns_applied_and_stamped(tmp_path) -> None:
    db = tmp_path / "test.db"
    conn = _connect(db)
    migrations_dir = _prepare_migrations_dir(
        tmp_path, "001_users.sql", "CREATE TABLE users (id INT PRIMARY KEY, name TEXT);"
    )

    applied, stamped = run_migrations(conn, migrations_dir=migrations_dir)

    assert applied == 1
    assert stamped == 0
    conn.close()


def _prepare_migrations_dir(tmp_path: Path, filename: str, content: str) -> Path:
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / filename).write_text(content)
    return migrations_dir
