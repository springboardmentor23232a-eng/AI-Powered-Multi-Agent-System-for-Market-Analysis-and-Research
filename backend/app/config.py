from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for backend (parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Application Settings for FinCrew.
    Automatically loads configuration from environment variables or .env file.
    """

    APP_NAME: str = "FinCrew"
    ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000

    # PostgreSQL Database URL (reads from backend/.env or environment variable; generic fallback for developers)
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/fincrew_db"

    # CORS Allowed Origins for Frontend (React / Vite)
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # JWT Authentication Settings (Module 1 Auth stage)
    SECRET_KEY: str = "default-insecure-key-must-be-set-in-env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse comma-separated strings into a list of allowed origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        # Check both backend/.env and current working directory .env
        env_file=(BASE_DIR / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Singleton instance of settings to import across the application
settings = Settings()

