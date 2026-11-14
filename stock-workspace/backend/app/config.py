import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stock_research.db")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-secret-change-me-please-32-bytes")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
COOKIE_NAME = "access_token"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]

MARKETS = ["NSE", "BSE", "NASDAQ", "NYSE"]
PERIODS = {"1M": 21, "3M": 63, "6M": 126, "1Y": 252, "5Y": 1260}  # approx. trading days
