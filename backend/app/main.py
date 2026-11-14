from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import secrets
from app.core.config import settings
from app.database import Base, engine
from app import models
from app.routers import auth, research, watchlist, preferences, stocks

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="1.0.0", description="User workspace API for the Multi-Agent Stock Research Analyst")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], allow_headers=["Content-Type", "X-CSRF-Token", "Authorization"])
app.include_router(auth.router, prefix="/api")
app.include_router(research.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(preferences.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")

@app.middleware("http")
async def csrf_protection(request, call_next):
    # Double-submit CSRF protection for authenticated cookie-based mutations.
    safe_methods = {"GET", "HEAD", "OPTIONS"}
    public_auth = {"/api/auth/register", "/api/auth/login", "/api/auth/google"}
    if request.method not in safe_methods and request.url.path not in public_auth and request.cookies.get("access_token"):
        cookie_token = request.cookies.get("csrf_token", "")
        header_token = request.headers.get("X-CSRF-Token", "")
        if not cookie_token or not header_token or not secrets.compare_digest(cookie_token, header_token):
            return JSONResponse(status_code=403, content={"detail": "CSRF validation failed. Refresh and try again."})
    return await call_next(request)

@app.get("/api/health")
def health():
    return {"status": "ok", "application": settings.app_name}
