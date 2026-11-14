from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
