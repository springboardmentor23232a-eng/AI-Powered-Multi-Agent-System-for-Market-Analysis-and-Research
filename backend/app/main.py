from contextlib import asynccontextmanager

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from . import models  # Import models before create_all so SQLAlchemy knows every table.
from .config import settings
from .database import Base, engine
from .routers.auth import router as auth_router
from .routers.market_data import router as market_data_router
from .routers.workspace import router as workspace_router
from .services.yahoo_finance import yahoo_finance_service

import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Convenient for this learning project. Use Alembic migrations for production.
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        logger.warning("Database connection on startup skipped or offline: %s", exc)
    yield



app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="Authentication and research workspace APIs.",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    same_site=settings.cookie_samesite,
    https_only=settings.cookie_secure,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
)

app.include_router(auth_router)
app.include_router(workspace_router)
app.include_router(market_data_router)

LANDING_PAGE_PATH = Path(__file__).resolve().parents[2] / "landing.html"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index():
    if LANDING_PAGE_PATH.is_file():
        return FileResponse(LANDING_PAGE_PATH)
    return HTMLResponse("<h1>Stock Research Analyst API</h1><p>Visit <a href='/docs'>/docs</a> for interactive API documentation.</p>")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name}
