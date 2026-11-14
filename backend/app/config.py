import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Multi-Agent Stock Research Analyst"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Secret Key for JWT Signing
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "super-secret-stock-research-analyst-key-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database URL: default SQLite for zero-configuration startup, supports PostgreSQL seamlessly
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./stock_research.db")
    
    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
