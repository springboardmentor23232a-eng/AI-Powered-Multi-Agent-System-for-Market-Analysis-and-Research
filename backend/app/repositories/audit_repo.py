import json


def log_event(conn, actor_user_id: int | None, action: str, target_type: str | None = None,
              target_id: str | int | None = None, status: str = "success",
              details: dict | None = None, ip_address: str | None = None) -> None:
    """Insert an audit log entry. Never pass passwords/tokens in details."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, status, details, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                actor_user_id,
                action,
                target_type,
                str(target_id) if target_id is not None else None,
                status,
                json.dumps(details) if details else None,
                ip_address,
            ),
        )


def query_logs(conn, actor_user_id: int | None = None, action: str | None = None,
               status_filter: str | None = None, target_type: str | None = None,
               date_from=None, date_to=None, allowed_actor_ids: list[int] | None = None,
               page: int = 1, page_size: int = 50):
    where, params = [], []
    if actor_user_id is not None:
        where.append("a.actor_user_id = %s")
        params.append(actor_user_id)
    if allowed_actor_ids is not None:
        where.append("a.actor_user_id = ANY(%s)")
        params.append(allowed_actor_ids)
    if action:
        where.append("a.action ILIKE %s")
        params.append(f"%{action}%")
    if status_filter:
        where.append("a.status = %s")
        params.append(status_filter)
    if target_type:
        where.append("a.target_type = %s")
        params.append(target_type)
    if date_from:
        where.append("a.timestamp >= %s")
        params.append(date_from)
    if date_to:
        where.append("a.timestamp <= %s")
        params.append(date_to)
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS total FROM audit_logs a {where_sql}", params)
        total = cur.fetchone()["total"]
        cur.execute(
            f"""
            SELECT a.id, a.actor_user_id, u.username AS actor_username, u.full_name AS actor_full_name,
                   a.action, a.target_type, a.target_id, a.status, a.details, a.ip_address, a.timestamp
            FROM audit_logs a
            LEFT JOIN users u ON u.id = a.actor_user_id
            {where_sql}
            ORDER BY a.timestamp DESC
            LIMIT %s OFFSET %s
            """,
            params + [page_size, (page - 1) * page_size],
        )
        rows = cur.fetchall()
    return rows, total
