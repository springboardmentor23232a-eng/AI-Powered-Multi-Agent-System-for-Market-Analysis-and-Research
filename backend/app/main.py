import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.database import init_db
from app.routes import auth_routes, oauth_routes, stock_routes, dashboard_routes

load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize and verify database connection
    print("\n[STARTUP] Starting Multi-Agent Stock Research Analyst Backend...")
    try:
        init_db()
        print("[STARTUP] Database connection and schema verification successful.\n")
    except Exception as e:
        print(f"[STARTUP ERROR] Could not connect to PostgreSQL: {e}\n")
    yield
    # Shutdown
    print("\n[SHUTDOWN] Stopping Multi-Agent Stock Research Analyst Backend...")


app = FastAPI(
    title="Multi-Agent Stock Research Analyst API",
    description="Backend API for Multi-Agent Stock Research Analyst - Module 1: User Authentication & Workspace",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for React Frontend
origins = [
    FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_routes.router)
app.include_router(oauth_routes.router)
app.include_router(stock_routes.router)
app.include_router(dashboard_routes.router)


@app.get("/", tags=["Health Check"])
def health_check():
    """
    Health check endpoint returning system status and database target.
    """
    return {
        "status": "online",
        "service": "Multi-Agent Stock Research Analyst API",
        "database": "multi_agent_stock_db",
        "version": "1.0.0",
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

