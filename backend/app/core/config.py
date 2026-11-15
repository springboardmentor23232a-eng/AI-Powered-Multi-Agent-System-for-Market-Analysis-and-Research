"""Application settings, loaded from environment variables (or a local .env file).

Keeping every secret and environment-specific value here means the code never
contains passwords or keys. See backend/.env.example for the list of variables.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Placeholder used in .env.example; the app refuses to start in production with it.
INSECURE_DEFAULT_SECRET = "change-me-to-a-long-random-string"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Multi-Agent Stock Research Analyst"
    environment: str = Field(default="development", description="development | test | production")
    api_prefix: str = "/api/v1"

    # Database: PostgreSQL in normal use, SQLite allowed for quick local runs and tests.
    database_url: str = "postgresql+psycopg://stockapp:stockapp@localhost:5432/stock_research"

    # JWT settings
    jwt_secret_key: str = INSECURE_DEFAULT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, gt=0)

    # Comma-separated list of frontend origins allowed to call the API.
    cors_origins: str = "http://localhost:5173"

    @field_validator("jwt_secret_key")
    @classmethod
    def secret_must_be_long_enough(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def assert_safe_for_production(self) -> None:
        if self.environment == "production" and self.jwt_secret_key == INSECURE_DEFAULT_SECRET:
            raise RuntimeError("Set a real JWT_SECRET_KEY before running in production")


@lru_cache
def get_settings() -> Settings:
    """Return one shared Settings object (read from the environment once)."""
    return Settings()
