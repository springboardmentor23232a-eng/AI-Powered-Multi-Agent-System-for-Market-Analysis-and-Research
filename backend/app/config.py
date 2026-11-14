import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Locate backend/.env whether running from project root or backend folder
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Multi-Agent Stock Research Analyst"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # PostgreSQL Database URL loaded from .env
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/stock_research_db"

    # JWT Authentication Settings from .env
    SECRET_KEY: str = "infosys_stock_research_super_secret_key_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS Allowed Origins for React Frontend
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = str(ENV_PATH)
        extra = "ignore"

settings = Settings()

