import os
os.environ.pop("SSLKEYLOGFILE", None)

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent



class Settings(BaseSettings):
    app_name: str = "Stock Research Analyst API"
    database_url: str
    jwt_secret_key: str
    session_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    frontend_origin: str = "http://localhost:5173"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = (
        "http://localhost:8000/api/auth/google/callback"
    )

    # Yahoo Finance API configuration
    yahoo_finance_api_key: str = ""
    yahoo_finance_api_host: str = "yahoo-finance15.p.rapidapi.com"
    yahoo_finance_base_url: str = "https://query1.finance.yahoo.com"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

