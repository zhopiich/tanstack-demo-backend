import sqlite3

from app.db.migrate import run_migrations
from app.db.session import connect_database


def test_001_initial_creates_all_eleven_tables(tmp_path) -> None:
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row

    run_migrations(conn)

    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    expected_tables = {
        "schema_migrations",
        "submitters",
        "auth_users",
        "auth_sessions",
        "submissions",
        "submission_tags",
        "submission_articles",
        "submission_images",
        "submission_videos",
        "submission_links",
        "reviews",
    }
    missing = expected_tables - tables
    assert not missing, f"Tables missing after 001_initial: {missing}"
    conn.close()


def test_001_initial_has_correct_column_types(tmp_path) -> None:
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    run_migrations(conn)

    cols = {
        (r["name"], r["type"])
        for r in conn.execute("PRAGMA table_info(submissions)").fetchall()
    }
    assert ("id", "TEXT") in cols
    assert ("title", "TEXT") in cols
    assert ("status", "TEXT") in cols
    assert ("score", "INTEGER") in cols
    assert ("thumbnail_url", "TEXT") in cols

    conn.close()


def test_001_initial_thumbnail_url_is_nullable(tmp_path) -> None:
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    run_migrations(conn)

    for r in conn.execute("PRAGMA table_info(submissions)").fetchall():
        if r["name"] == "thumbnail_url":
            assert r["notnull"] == 0, "thumbnail_url should be nullable"
            return

    conn.close()


def test_001_initial_has_expected_foreign_keys(tmp_path) -> None:
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    run_migrations(conn)

    fk_list = conn.execute("PRAGMA foreign_key_list(submissions)").fetchall()
    target_tables = {r["table"] for r in fk_list}
    assert "submitters" in target_tables

    pk_cols = [
        r["name"]
        for r in conn.execute("PRAGMA table_info(submission_tags)").fetchall()
        if r["pk"]
    ]
    assert pk_cols == ["submission_id", "position"]

    conn.close()


def test_001_initial_is_recorded_in_schema_migrations(tmp_path) -> None:
    db = tmp_path / "test.db"
    conn = connect_database(db)
    run_migrations(conn)

    row = conn.execute(
        "SELECT version, filename FROM schema_migrations WHERE version=1"
    ).fetchone()
    assert row is not None
    assert row["version"] == 1
    assert row["filename"] == "001_initial.sql"
    conn.close()
