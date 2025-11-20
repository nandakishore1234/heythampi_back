from __future__ import annotations

from fastapi import FastAPI

from app.core.config import settings


def create_application() -> FastAPI:
    app = FastAPI(title=settings.project_name)

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_application()
