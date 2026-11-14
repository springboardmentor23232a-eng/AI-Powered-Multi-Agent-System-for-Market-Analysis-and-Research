"""Create the initial administrator account.

Reads credentials from environment variables / .env:
    ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_FULL_NAME

Usage (from backend/ directory):
    python scripts/create_admin.py

Safe to re-run: exits with a message if the username or email already exists.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from app.config import settings  # noqa: E402
from app.database import get_connection, init_pool, put_connection  # noqa: E402
from app.repositories import user_repo  # noqa: E402
from app.security import hash_password  # noqa: E402


def main() -> int:
    if not settings.ADMIN_PASSWORD:
        print("ERROR: ADMIN_PASSWORD is not set. Configure it in backend/.env first.")
        return 1

    init_pool()
    conn = get_connection()
    try:
        existing = user_repo.find_by_identifier(conn, settings.ADMIN_USERNAME) or \
            user_repo.find_by_identifier(conn, settings.ADMIN_EMAIL)
        if existing:
            print(f"Admin account already exists (user id={existing['id']}, username={existing['username']}).")
            return 0

        user_id = user_repo.create_user(
            conn,
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            full_name=settings.ADMIN_FULL_NAME,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
        )
        # Assign administrator role
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM roles WHERE role_name = 'administrator'")
            role = cur.fetchone()
            if role is None:
                print("ERROR: 'administrator' role not found. Run migrations/001_init.sql first.")
                conn.rollback()
                return 1
            cur.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                (user_id, role["id"]),
            )
        conn.commit()
        print(f"Admin account created: username={settings.ADMIN_USERNAME} email={settings.ADMIN_EMAIL} id={user_id}")
        return 0
    finally:
        put_connection(conn)


if __name__ == "__main__":
    raise SystemExit(main())
