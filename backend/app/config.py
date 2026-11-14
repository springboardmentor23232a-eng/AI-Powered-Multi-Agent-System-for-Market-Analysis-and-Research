import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()

# Either set DATABASE_URL directly, or set the DB_* values below.
# Using DB_* is safer because the password can contain any characters.
DATABASE_URL = os.getenv("DATABASE_URL") or URL.create(
    "postgresql+psycopg2",
    username=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", ""),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "stock_research"),
)
SECRET_KEY = os.environ["SECRET_KEY"]
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
