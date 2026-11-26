from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import Base, engine
from .routers import analysis, auth, market, preferences, research, watchlist


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)  # creates missing tables (use Alembic migrations in production)
    yield


app = FastAPI(title="Multi-Agent Stock Research Analyst", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("Cache-Control", "no-store")
    if settings.cookie_secure:  # only meaningful (and only sent) when running behind HTTPS
        resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return resp


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    """Flatten Pydantic errors to readable messages: {"detail": "...", "errors": {"field": "msg"}}"""
    errors = {}
    for e in exc.errors():
        field = ".".join(str(p) for p in e["loc"] if p not in ("body", "query", "path")) or "request"
        msg = e["msg"].removeprefix("Value error, ")
        errors.setdefault(field, msg)
    return JSONResponse(status_code=422, content={"detail": next(iter(errors.values())), "errors": errors})


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok"}


for r in (auth.router, preferences.router, research.router, watchlist.router, market.router, analysis.router):
    app.include_router(r)
