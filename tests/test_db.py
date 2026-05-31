import sqlite3

from app.db.session import initialize_database


def test_initialize_database_creates_schema_and_seed_data(tmp_path) -> None:
    connection = initialize_database(tmp_path / "content.db")

    tables = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }

    assert {
        "submitters",
        "submissions",
        "submission_tags",
        "submission_articles",
        "submission_images",
        "submission_videos",
        "submission_links",
        "reviews",
    }.issubset(tables)
    assert _count(connection, "submitters") == 3
    assert _count(connection, "submissions") == 4
    assert _count(connection, "submission_tags") == 7
    assert _count(connection, "submission_articles") == 1
    assert _count(connection, "submission_images") == 1
    assert _count(connection, "submission_videos") == 1
    assert _count(connection, "submission_links") == 1
    assert _count(connection, "reviews") == 0


def test_initialize_database_rebuilds_existing_database(tmp_path) -> None:
    database_path = tmp_path / "content.db"
    connection = initialize_database(database_path)
    connection.execute(
        """
        INSERT INTO submitters (id, name, email, tier)
        VALUES ('c999999999999999999999999', 'Temp User', 'temp@example.com', 'free')
        """
    )
    connection.commit()
    connection.close()

    rebuilt_connection = initialize_database(database_path)

    assert _count(rebuilt_connection, "submitters") == 3
    assert (
        rebuilt_connection.execute(
            "SELECT COUNT(*) AS count FROM submitters WHERE email = 'temp@example.com'"
        ).fetchone()["count"]
        == 0
    )


def _count(connection: sqlite3.Connection, table: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    return row["count"]
