import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Multi-Agent Stock Research Analyst"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # Environment & CORS
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres@localhost:5432/stock_research_db"
    
    # Security & Tokens
    SECRET_KEY: str = "9f83a45c829e5a1b32d4e78f01c4b2a95d7e3f1a6c8b0d2e4f6a8c0e2b4d6f8a"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Market & Analysis Defaults
    DEFAULT_MARKET: str = "NASDAQ"
    DEFAULT_ANALYSIS_PERIOD: str = "1 Year"
    
    # Supported Options
    SUPPORTED_MARKETS: List[str] = ["NSE", "BSE", "NASDAQ", "NYSE"]
    SUPPORTED_PERIODS: List[str] = ["1 Month", "3 Months", "6 Months", "1 Year", "5 Years"]

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

