import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import init_db, verify_connection
from app.routes.auth import router as auth_router
from app.routes.stocks import router as stocks_router
from app.routes.research import router as research_router
from app.routes.watchlist import router as watchlist_router
from app.routes.preference import router as preference_router
from app.routes.dataset import router as dataset_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager:
    Initializes and verifies database connection and tables on startup.
    """
    logger.info("Initializing database connection and schema...")
    init_db()
    diag = verify_connection()
    logger.info(
        f"Database connected successfully ({diag['dialect']}://{diag['host']}:{diag['port']}/{diag['database']}). "
        f"Verified tables: {diag['tables']}"
    )
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Multi-Agent Stock Research Analyst (Infosys Internship Project)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handlers ────────────────────────────────────────────────
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url.path),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Extracts friendly error messages from Pydantic validation failures.
    """
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        msg = err.get("msg", "Invalid value")
        # Strip internal Pydantic prefix if present
        if msg.startswith("Value error, "):
            msg = msg.replace("Value error, ", "")
        errors.append({"field": field or "payload", "message": msg})

    first_msg = errors[0]["message"] if errors else "Invalid request data."

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "validation_error",
            "detail": first_msg,
            "errors": errors,
            "path": str(request.url.path),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    # Security: Never expose internal server traces or database credentials to the client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "server_error",
            "detail": "An internal server error occurred. Please try again later.",
            "path": str(request.url.path),
        },
    )


# ── Include Routers ──────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api")
app.include_router(stocks_router, prefix="/api")
app.include_router(research_router, prefix="/api")
app.include_router(watchlist_router, prefix="/api")
app.include_router(preference_router, prefix="/api")
app.include_router(dataset_router, prefix="/api")


# ── Diagnostics & Root Endpoints ─────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }

