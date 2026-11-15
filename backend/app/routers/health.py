from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", summary="Basic API Health Check")
def health_check():
    """
    Returns general application status and environment information.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENV,
        "version": "1.0.0",
    }


@router.get("/db-health", summary="Database Connection Health Check")
def db_health_check(db: Session = Depends(get_db)):
    """
    Executes a real query against PostgreSQL to verify database connectivity.
    """
    try:
        query = text("SELECT current_database(), current_user, version();")
        result = db.execute(query).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database query returned no data.",
            )

        return {
            "status": "connected",
            "database": result[0],
            "user": result[1],
            "postgres_version": result[2],
            "details": "PostgreSQL database connection is healthy",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "disconnected",
                "error": str(exc),
                "details": "Failed to connect to the PostgreSQL database",
            },
        )

