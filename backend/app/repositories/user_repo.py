def find_by_identifier(conn, identifier: str):
    """Find a user by username OR email (case-insensitive email)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, username, email, full_name, password_hash, status, created_at, updated_at
            FROM users
            WHERE username = %s OR lower(email) = lower(%s)
            LIMIT 1
            """,
            (identifier, identifier),
        )
        return cur.fetchone()


def get_user_auth_profile(conn, user_id: int):
    """Fetch user plus role names and permission codes for auth context."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.id, u.username, u.email, u.full_name, u.status,
                   COALESCE(array_agg(DISTINCT r.role_name) FILTER (WHERE r.role_name IS NOT NULL), '{}') AS roles,
                   COALESCE(array_agg(DISTINCT p.permission_code) FILTER (WHERE p.permission_code IS NOT NULL), '{}') AS permissions
            FROM users u
            LEFT JOIN user_roles ur ON ur.user_id = u.id
            LEFT JOIN roles r ON r.id = ur.role_id
            LEFT JOIN role_permissions rp ON rp.role_id = r.id
            LEFT JOIN permissions p ON p.id = rp.permission_id
            WHERE u.id = %s
            GROUP BY u.id
            """,
            (user_id,),
        )
        return cur.fetchone()


def get_user_by_id(conn, user_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, username, email, full_name, status, created_at, updated_at
            FROM users WHERE id = %s
            """,
            (user_id,),
        )
        return cur.fetchone()


def list_users(conn, search: str | None = None, status_filter: str | None = None,
               page: int = 1, page_size: int = 20):
    where, params = [], []
    if search:
        where.append("(u.username ILIKE %s OR u.email ILIKE %s OR u.full_name ILIKE %s)")
        like = f"%{search}%"
        params += [like, like, like]
    if status_filter:
        where.append("u.status = %s")
        params.append(status_filter)
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT COUNT(*) AS total FROM users u {where_sql}
            """,
            params,
        )
        total = cur.fetchone()["total"]

        cur.execute(
            f"""
            SELECT u.id, u.username, u.email, u.full_name, u.status, u.created_at, u.updated_at,
                   COALESCE(array_agg(DISTINCT r.role_name) FILTER (WHERE r.role_name IS NOT NULL), '{{}}') AS roles,
                   COALESCE(array_agg(DISTINCT r.id) FILTER (WHERE r.id IS NOT NULL), '{{}}') AS role_ids
            FROM users u
            LEFT JOIN user_roles ur ON ur.user_id = u.id
            LEFT JOIN roles r ON r.id = ur.role_id
            {where_sql}
            GROUP BY u.id
            ORDER BY u.created_at DESC
            LIMIT %s OFFSET %s
            """,
            params + [page_size, (page - 1) * page_size],
        )
        rows = cur.fetchall()
    return rows, total


def create_user(conn, username: str, email: str, full_name: str, password_hash: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (username, email, full_name, password_hash)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (username, email, full_name, password_hash),
        )
        return cur.fetchone()["id"]


def update_user(conn, user_id: int, fields: dict) -> None:
    if not fields:
        return
    sets = ", ".join(f"{k} = %s" for k in fields)
    sets += ", updated_at = now()"
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE users SET {sets} WHERE id = %s",
            list(fields.values()) + [user_id],
        )


def set_user_status(conn, user_id: int, status: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET status = %s, updated_at = now() WHERE id = %s",
            (status, user_id),
        )


def set_user_password(conn, user_id: int, password_hash: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET password_hash = %s, updated_at = now() WHERE id = %s",
            (password_hash, user_id),
        )


def replace_user_roles(conn, user_id: int, role_ids: list[int]) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
        for rid in role_ids:
            cur.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (user_id, rid),
            )


def get_user_roles(conn, user_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.id, r.role_name, r.description
            FROM user_roles ur JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = %s ORDER BY r.role_name
            """,
            (user_id,),
        )
        return cur.fetchall()


def list_active_users_excluding(conn, exclude_ids: list[int]):
    """Active users not in exclude_ids — used for team member candidate lists."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, username, email, full_name, status
            FROM users
            WHERE status = 'active' AND id <> ALL(%s)
            ORDER BY username
            """,
            (exclude_ids or [-1],),
        )
        return cur.fetchall()


def user_exists(conn, user_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE id = %s", (user_id,))
        return cur.fetchone() is not None
