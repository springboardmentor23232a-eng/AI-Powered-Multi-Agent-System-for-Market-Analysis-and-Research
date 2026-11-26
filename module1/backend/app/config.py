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

    # --- "Continue with Google / Apple" (leave blank to hide/disable the button) ---
    public_base_url: str = "http://localhost:5173"   # where the BROWSER reaches the app (Vite dev server / your domain)
    google_client_id: str = ""
    google_client_secret: str = ""
    apple_client_id: str = ""      # the Services ID, e.g. com.example.stockresearch.web
    apple_team_id: str = ""
    apple_key_id: str = ""
    apple_private_key: str = ""    # contents of the .p8 file; newlines may be written as \n

    # Kaggle "Financial Statements of Major Companies (2009-2023)" CSV (optional; default backend/data/financial_statements.csv)
    financials_dataset_path: str = ""

    market_data_provider: str = "demo"  # "demo" | "yahoo"
    news_provider: str = "demo"         # "demo" (clearly-labelled SAMPLE headlines) | "yahoo" (RSS, no key) | "newsapi" (needs NEWSAPI_KEY)
    newsapi_key: str = ""
    workflow_delay_seconds: float = 3.0
    bcrypt_rounds: int = 12


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.cookie_secure and s.secret_key == _DEFAULT_SECRET:
        raise RuntimeError("Set a real SECRET_KEY before running with COOKIE_SECURE=true (production).")
    return s


settings = get_settings()
