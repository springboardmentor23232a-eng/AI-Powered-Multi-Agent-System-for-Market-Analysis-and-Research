import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# Token expiration time
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

# Check whether required variables exist
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from .env file")

if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is missing from .env file")

if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID is missing from .env file")