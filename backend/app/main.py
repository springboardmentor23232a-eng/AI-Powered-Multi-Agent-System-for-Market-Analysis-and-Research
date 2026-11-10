import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import auth, research, stocks, workspace
from app.core.config import settings, validate_production
from app.core.database import SessionLocal, engine
from app.core.logging import configure_logging
from app.services.maintenance import reconcile_stale_tasks

log = logging.getLogger("veritas.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_production(settings)
    configure_logging(settings.log_level)
    reconcile_stale_tasks(SessionLocal, settings.stale_task_minutes)
    yield


app = FastAPI(title="Veritas Equity Research API", version="0.1.0", lifespan=lifespan,
              docs_url=None if settings.is_production else "/docs",
              redoc_url=None, openapi_url=None if settings.is_production else "/openapi.json")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def access_log(request: Request, call_next):
    rid, t0 = uuid.uuid4().hex[:12], time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception("unhandled error", extra={"request_id": rid, "method": request.method, "path": request.url.path})
        raise
    response.headers["X-Request-ID"] = rid
    log.info("request", extra={"request_id": rid, "method": request.method, "path": request.url.path,
                               "status": response.status_code, "duration_ms": round((time.perf_counter() - t0) * 1000, 1)})
    return response


app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(research.router)
app.include_router(workspace.router)


@app.get("/")
def root():
    return {
        "app": "Veritas Equity Research API",
        "version": "0.1.0",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/health",
        "frontend_url": "http://localhost:5173",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
    except Exception:
        raise HTTPException(503, "Database unavailable")
    return {"status": "ready"}
