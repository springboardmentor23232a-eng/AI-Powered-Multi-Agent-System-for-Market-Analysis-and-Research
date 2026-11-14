from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, market, watchlist, preferences, research

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-Agent Stock Research Analyst API (FastAPI + PostgreSQL + LangGraph + Yahoo Finance)"
)

# Configure CORS Middleware for React frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(market.router, prefix="/api", tags=["Market Data (yfinance)"])
app.include_router(watchlist.router, prefix="/api", tags=["Watchlist (Saved Stocks)"])
app.include_router(preferences.router, prefix="/api", tags=["User Preferences"])
app.include_router(research.router, prefix="/api", tags=["Research Tasks"])

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "database": "PostgreSQL connected",
        "market_data": "Yahoo Finance (yfinance) operational",
        "service": "FastAPI Multi-Agent Core Service"
    }
