from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Multi-Agent Stock Research Analyst"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://stock_user:change_this_local_password@localhost:5432/stock_research_db"
    jwt_secret_key: str = "development-only-change-this-secret-before-deployment"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    google_client_id: str = ""
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
