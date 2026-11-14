from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file (backend/.env) so the backend works
# regardless of the directory Uvicorn is launched from.
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "netshield"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = ""

    JWT_SECRET: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: str = "http://localhost:5173"
    COOKIE_SECURE: bool = False

    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@netshield.local"
    ADMIN_PASSWORD: str = ""
    ADMIN_FULL_NAME: str = "System Administrator"


settings = Settings()
