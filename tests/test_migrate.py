import hashlib
import sqlite3

import pytest

from app.db.migrate import (
    compute_hash,
    extract_table_names_from_sql,
    get_migration_files,
    has_any_table,
)


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
    conn = sqlite3.connect(str(db))
    assert has_any_table(conn) is False
    conn.close()


def test_has_any_table_returns_true_when_table_exists(tmp_path) -> None:
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
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
