from fastapi import FastAPI

from app.core.errors import register_error_handlers
from app.routers import auth


def create_app() -> FastAPI:
    app = FastAPI(title="Content API", version="1.0.0")
    register_error_handlers(app)
    app.include_router(auth.router, prefix="/api")

    @app.get("/")
    def root() -> dict[str, str]:
        return {"message": "Hello World"}

    return app


app = create_app()
