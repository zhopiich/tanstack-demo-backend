import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> Settings:
        source = os.environ if environ is None else environ
        return cls(database_path=Path(source.get("DATABASE_PATH", "data/app.db")))


def get_settings() -> Settings:
    return Settings.from_environment()
