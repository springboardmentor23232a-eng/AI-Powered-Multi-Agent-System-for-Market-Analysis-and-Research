from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routes import auth_routes, preferences_routes, watchlist_routes, research_routes

# Initialize database schema tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for Multi-Agent Stock Research Analyst - Module 1: Authentication & Workspace"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_routes.router, prefix=settings.API_PREFIX)
app.include_router(preferences_routes.router, prefix=settings.API_PREFIX)
app.include_router(watchlist_routes.router, prefix=settings.API_PREFIX)
app.include_router(research_routes.router, prefix=settings.API_PREFIX)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "module": "Module 1 - User Authentication & Research Workspace",
        "docs": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
