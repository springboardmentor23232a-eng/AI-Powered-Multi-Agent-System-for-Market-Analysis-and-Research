from datetime import datetime, timedelta, timezone

from ..security import hash_token


def create_refresh_token(conn, user_id: int, raw_token: str, expires_at) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (user_id, hash_token(raw_token), expires_at),
        )
        return cur.fetchone()["id"]


def get_valid_refresh_token(conn, raw_token: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, expires_at, revoked
            FROM refresh_tokens
            WHERE token_hash = %s
            """,
            (hash_token(raw_token),),
        )
        return cur.fetchone()


def revoke_token(conn, token_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE refresh_tokens SET revoked = TRUE WHERE id = %s", (token_id,))


def revoke_all_user_tokens(conn, user_id: int) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE refresh_tokens SET revoked = TRUE WHERE user_id = %s AND revoked = FALSE",
            (user_id,),
        )
        return cur.rowcount


def cleanup_expired(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM refresh_tokens WHERE expires_at < now()")
        return cur.rowcount


def refresh_expiry() -> datetime:
    from ..config import settings
    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
