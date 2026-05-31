import sqlite3
import threading

from app.db.session import connect_database, initialize_runtime_database, reset_database


def test_reset_database_creates_schema_and_seed_data(tmp_path) -> None:
    database_path = tmp_path / "content.db"

    reset_database(database_path)

    connection = connect_database(database_path)
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

    submitter = connection.execute(
        """
        SELECT id, name, email, tier
        FROM submitters
        WHERE email = 'alex@example.com'
        """
    ).fetchone()
    assert dict(submitter) == {
        "id": "c100000000000000000000001",
        "name": "Alex Chen",
        "email": "alex@example.com",
        "tier": "pro",
    }

    article = connection.execute(
        """
        SELECT
            s.id,
            s.title,
            s.status,
            s.content_type,
            s.content_url,
            s.thumbnail_url,
            s.score,
            s.flag_count,
            a.word_count,
            a.reading_time
        FROM submissions AS s
        JOIN submission_articles AS a ON a.submission_id = s.id
        WHERE s.id = 'c200000000000000000000001'
        """
    ).fetchone()
    assert dict(article) == {
        "id": "c200000000000000000000001",
        "title": "Article moderation guide",
        "status": "pending",
        "content_type": "article",
        "content_url": "https://example.com/articles/moderation-guide",
        "thumbnail_url": None,
        "score": 82,
        "flag_count": 0,
        "word_count": 1800,
        "reading_time": 9,
    }
    connection.close()


def test_reset_database_rebuilds_existing_database(tmp_path) -> None:
    database_path = tmp_path / "content.db"
    reset_database(database_path)
    connection = connect_database(database_path)
    connection.execute(
        """
        INSERT INTO submitters (id, name, email, tier)
        VALUES ('c999999999999999999999999', 'Temp User', 'temp@example.com', 'free')
        """
    )
    connection.commit()
    connection.close()

    reset_database(database_path)
    rebuilt_connection = connect_database(database_path)

    assert _count(rebuilt_connection, "submitters") == 3
    assert (
        rebuilt_connection.execute(
            "SELECT COUNT(*) AS count FROM submitters WHERE email = 'temp@example.com'"
        ).fetchone()["count"]
        == 0
    )
    rebuilt_connection.close()


def test_initialize_runtime_database_creates_database_when_missing(tmp_path) -> None:
    database_path = tmp_path / "runtime.db"

    initialize_runtime_database(database_path)

    assert database_path.exists()
    connection = connect_database(database_path)
    assert _count(connection, "submissions") == 4
    connection.close()


def test_initialize_runtime_database_keeps_existing_database(tmp_path) -> None:
    database_path = tmp_path / "runtime.db"
    initialize_runtime_database(database_path)
    connection = connect_database(database_path)
    connection.execute(
        """
        INSERT INTO submitters (id, name, email, tier)
        VALUES ('c999999999999999999999999', 'Temp User', 'temp@example.com', 'free')
        """
    )
    connection.commit()
    connection.close()

    initialize_runtime_database(database_path)
    existing_connection = connect_database(database_path)

    assert (
        existing_connection.execute(
            "SELECT COUNT(*) AS count FROM submitters WHERE email = 'temp@example.com'"
        ).fetchone()["count"]
        == 1
    )
    existing_connection.close()


def test_connect_database_uses_default_sqlite_thread_check(tmp_path) -> None:
    database_path = tmp_path / "content.db"
    reset_database(database_path)
    connection = connect_database(database_path)
    errors: list[BaseException] = []

    def use_connection_from_another_thread() -> None:
        try:
            connection.execute("SELECT 1")
        except BaseException as error:
            errors.append(error)

    thread = threading.Thread(target=use_connection_from_another_thread)
    thread.start()
    thread.join()
    connection.close()

    assert len(errors) == 1
    assert isinstance(errors[0], sqlite3.ProgrammingError)
    assert "SQLite objects created in a thread" in str(errors[0])


def test_db_seed_does_not_depend_on_inmemory_store() -> None:
    import app.db.seed as seed_module

    removed_module = "app.stores." + "submission" + "_store"
    removed_helper = "seed_" + "submissions"

    assert removed_module not in seed_module.__dict__.values()
    assert not hasattr(seed_module, removed_helper)


def _count(connection: sqlite3.Connection, table: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    return row["count"]
