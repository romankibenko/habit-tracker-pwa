"""Точка входа FastAPI-приложения.

Бэкенд и фронтенд в одном репозитории — FastAPI раздаёт и API
(префикс /api), и статический фронтенд из папки ./static.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.auth import make_get_current_user
from app.config import load_config
from app.database import Database
from app.push import PushService
from app.routes import auth_routes, checkins_routes, habits_routes, push_routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def create_app() -> FastAPI:
    config = load_config()
    database = Database(config.database)
    push_service = PushService(config.vapid)
    get_current_user = make_get_current_user(config.jwt)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await database.connect()
        logger.info("habit-tracker-pwa запущен")
        yield
        await database.disconnect()
        logger.info("habit-tracker-pwa остановлен")

    app = FastAPI(
        title="Habit Tracker PWA",
        description="Трекер привычек на FastAPI + чистый JS + PWA",
        version="1.0.0",
        lifespan=lifespan,
    )

    # API роутеры
    app.include_router(auth_routes.build_router(database, config.jwt))
    app.include_router(habits_routes.build_router(database, get_current_user))
    app.include_router(checkins_routes.build_router(database, get_current_user))
    app.include_router(
        push_routes.build_router(database, push_service, config.vapid, get_current_user)
    )

    # Health-check
    @app.get("/api/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    # Статика: всё что не /api отдаётся из ./static
    if STATIC_DIR.exists():
        app.mount(
            "/static", StaticFiles(directory=STATIC_DIR), name="static-assets"
        )

        @app.get("/")
        async def index() -> FileResponse:
            return FileResponse(STATIC_DIR / "index.html")

        @app.get("/manifest.json")
        async def manifest() -> FileResponse:
            return FileResponse(STATIC_DIR / "manifest.json")

        @app.get("/service-worker.js")
        async def service_worker() -> FileResponse:
            return FileResponse(
                STATIC_DIR / "service-worker.js",
                media_type="application/javascript",
            )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    config = load_config()
    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=True,
    )
