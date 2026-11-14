from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import close_pool, init_pool
from .routers import audit, auth, dashboard, roles, teams, users

app = FastAPI(
    title="NetShield AI API",
    description="AI-Powered Network Anomaly Detection and Predictive Intrusion Monitoring Platform - Module 1: User Management",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(roles.router, prefix=API_PREFIX)
app.include_router(teams.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)


@app.on_event("startup")
def startup():
    init_pool()


@app.on_event("shutdown")
def shutdown():
    close_pool()


@app.get("/health")
def health():
    return {"status": "ok", "service": "netshield-ai-api"}
