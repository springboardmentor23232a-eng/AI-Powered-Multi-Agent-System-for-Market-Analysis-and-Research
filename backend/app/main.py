"""FastAPI application entry point.

Run locally with:  uvicorn app.main:app --reload   (from the backend/ folder)
Interactive API docs are then at http://localhost:8000/docs
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSession
from app.api.routes import auth, research, users, watchlist
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    settings.assert_safe_for_production()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Module 1: user authentication and research workspace.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,  # we send the JWT in a header, not in cookies
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    for router in (auth.router, users.router, watchlist.router, research.router):
        app.include_router(router, prefix=settings.api_prefix)

    @app.get("/health", tags=["health"])
    def health_check(db: DbSession):
        """Liveness check that also confirms the database is reachable."""
        try:
            db.execute(text("SELECT 1"))
        except SQLAlchemyError:
            logger.exception("Health check: database unreachable")
            return JSONResponse(
                status_code=503, content={"status": "degraded", "database": "unreachable"}
            )
        return {"status": "ok", "database": "ok"}

    return app


app = create_app()
