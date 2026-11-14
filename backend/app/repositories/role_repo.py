def list_roles(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.id, r.role_name, r.description,
                   COALESCE(array_agg(DISTINCT p.permission_code) FILTER (WHERE p.permission_code IS NOT NULL), '{}') AS permissions
            FROM roles r
            LEFT JOIN role_permissions rp ON rp.role_id = r.id
            LEFT JOIN permissions p ON p.id = rp.permission_id
            GROUP BY r.id ORDER BY r.role_name
            """
        )
        return cur.fetchall()


def get_role(conn, role_id: int):
    with conn.cursor() as cur:
        cur.execute("SELECT id, role_name, description FROM roles WHERE id = %s", (role_id,))
        return cur.fetchone()


def list_permissions(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, permission_code, module, description FROM permissions ORDER BY module, permission_code"
        )
        return cur.fetchall()


def get_role_permissions(conn, role_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT p.id, p.permission_code, p.module, p.description
            FROM role_permissions rp
            JOIN permissions p ON p.id = rp.permission_id
            WHERE rp.role_id = %s
            ORDER BY p.module, p.permission_code
            """,
            (role_id,),
        )
        return cur.fetchall()


def set_role_permissions(conn, role_id: int, permission_ids: list[int]) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM role_permissions WHERE role_id = %s", (role_id,))
        for pid in permission_ids:
            cur.execute(
                "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (role_id, pid),
            )


def valid_permission_ids(conn, permission_ids: list[int]) -> bool:
    if not permission_ids:
        return True
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS c FROM permissions WHERE id = ANY(%s)",
            (permission_ids,),
        )
        return cur.fetchone()["c"] == len(set(permission_ids))


def valid_role_ids(conn, role_ids: list[int]) -> bool:
    if not role_ids:
        return True
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS c FROM roles WHERE id = ANY(%s)",
            (role_ids,),
        )
        return cur.fetchone()["c"] == len(set(role_ids))
