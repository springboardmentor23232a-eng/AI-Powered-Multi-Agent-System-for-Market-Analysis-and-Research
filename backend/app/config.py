from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_SECRET = "change-me-change-me-change-me-change-me-please"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/stockresearch"
    secret_key: str = _DEFAULT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    cookie_name: str = "access_token"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cors_origins: list[str] = ["http://localhost:5173"]
    expose_token_in_body: bool = True

    market_data_provider: str = "demo"  # "demo" | "yahoo"
    workflow_delay_seconds: float = 3.0
    bcrypt_rounds: int = 12


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.cookie_secure and s.secret_key == _DEFAULT_SECRET:
        raise RuntimeError("Set a real SECRET_KEY before running with COOKIE_SECURE=true (production).")
    return s


settings = get_settings()
