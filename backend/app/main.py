from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from . import models  # Import models before create_all so SQLAlchemy knows every table.
from .config import settings
from .database import Base, engine
from .routers.auth import router as auth_router
from .routers.workspace import router as workspace_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Convenient for this learning project. Use Alembic migrations for production.
    Base.metadata.create_all(bind=engine)
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


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name}
