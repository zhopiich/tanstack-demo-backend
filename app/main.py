from dataclasses import replace
from pathlib import Path

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.db.session import initialize_runtime_database
from app.routers import auth, dashboard, submissions


def create_app(database_path: str | Path | None = None) -> FastAPI:
    settings = get_settings()
    if database_path is not None:
        # Keep auth/token settings from the normal config path; constructing
        # Settings(database_path=...) would omit required non-DB fields.
        settings = replace(settings, database_path=Path(database_path))

    initialize_runtime_database(settings.database_path)

    app = FastAPI(title="Content API", version="1.0.0")
    app.state.settings = settings
    app.dependency_overrides[get_settings] = lambda: settings

    register_error_handlers(app)
    app.include_router(auth.router, prefix="/api")
    app.include_router(submissions.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")

    @app.get("/")
    def root() -> dict[str, str]:
        return {"message": "Hello World"}

    return app


app = create_app()
