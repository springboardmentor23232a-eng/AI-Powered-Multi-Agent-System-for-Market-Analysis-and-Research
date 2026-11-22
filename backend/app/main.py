import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.research import router as research_router

# Initialize FastAPI application with Swagger metadata
app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Agent Stock Research Analyst API – Module 1: User Authentication & Workspace | Module 2: Multi-Agent Stock Research",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"persistAuthorization": True},
)

# CORS Configuration for Frontend (React / Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(research_router)


@app.get("/", summary="Root Endpoint")
def root():
    """
    Root endpoint providing basic API info and navigation links.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/api/health",
        "db_health": "/api/db-health",
        "auth_endpoints": {
            "register": "POST /api/auth/register",
            "login": "POST /api/auth/login",
            "me": "GET /api/auth/me",
            "logout": "POST /api/auth/logout",
        },
        "research_endpoints": {
            "analyze": "POST /api/research/analyze",
            "create_session": "POST /api/research/sessions",
            "start_session": "POST /api/research/sessions/{session_id}/start",
            "list_sessions": "GET /api/research/sessions",
            "get_session": "GET /api/research/sessions/{session_id}",
            "get_report": "GET /api/research/sessions/{session_id}/report",
            "export_report": "GET /api/research/sessions/{session_id}/export",
            "compare": "POST /api/research/compare",
            "workspace_analytics": "GET /api/research/analytics/summary",
            "delete_session": "DELETE /api/research/sessions/{session_id}",
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
    )
