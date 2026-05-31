from app.core.config import Settings, get_settings


def test_settings_default_database_path() -> None:
    settings = Settings.from_environment({})

    assert settings.database_path.as_posix() == "data/app.db"


def test_settings_reads_database_path_from_environment() -> None:
    settings = Settings.from_environment({"DATABASE_PATH": "/tmp/content.db"})

    assert settings.database_path.as_posix() == "/tmp/content.db"


def test_get_settings_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_PATH", "/tmp/runtime.db")

    settings = get_settings()

    assert settings.database_path.as_posix() == "/tmp/runtime.db"
