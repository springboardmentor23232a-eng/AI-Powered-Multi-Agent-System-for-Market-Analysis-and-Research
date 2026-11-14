def create_team(conn, team_name: str, description: str | None, lead_user_id: int | None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO teams (team_name, description, lead_user_id)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (team_name, description, lead_user_id),
        )
        return cur.fetchone()["id"]


def get_team(conn, team_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT t.id, t.team_name, t.description, t.lead_user_id, t.created_at, t.updated_at,
                   u.username AS lead_username, u.full_name AS lead_full_name
            FROM teams t
            LEFT JOIN users u ON u.id = t.lead_user_id
            WHERE t.id = %s
            """,
            (team_id,),
        )
        return cur.fetchone()


def list_teams(conn):
    """List all teams (admin view)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT t.id, t.team_name, t.description, t.lead_user_id, t.created_at, t.updated_at,
                   u.username AS lead_username, u.full_name AS lead_full_name,
                   (SELECT COUNT(*) FROM team_members tm WHERE tm.team_id = t.id) AS member_count
            FROM teams t
            LEFT JOIN users u ON u.id = t.lead_user_id
            ORDER BY t.team_name
            """
        )
        return cur.fetchall()


def list_teams_for_user(conn, user_id: int, is_admin: bool, is_lead: bool):
    with conn.cursor() as cur:
        if is_admin:
            cur.execute(
                """
                SELECT t.id, t.team_name, t.description, t.lead_user_id, t.created_at, t.updated_at,
                       u.username AS lead_username, u.full_name AS lead_full_name,
                       (SELECT COUNT(*) FROM team_members tm WHERE tm.team_id = t.id) AS member_count
                FROM teams t
                LEFT JOIN users u ON u.id = t.lead_user_id
                ORDER BY t.team_name
                """
            )
        elif is_lead:
            cur.execute(
                """
                SELECT DISTINCT t.id, t.team_name, t.description, t.lead_user_id, t.created_at, t.updated_at,
                       u.username AS lead_username, u.full_name AS lead_full_name,
                       (SELECT COUNT(*) FROM team_members tm WHERE tm.team_id = t.id) AS member_count
                FROM teams t
                LEFT JOIN users u ON u.id = t.lead_user_id
                LEFT JOIN team_members tm ON tm.team_id = t.id
                WHERE t.lead_user_id = %s OR tm.user_id = %s
                ORDER BY t.team_name
                """,
                (user_id, user_id),
            )
        else:
            cur.execute(
                """
                SELECT t.id, t.team_name, t.description, t.lead_user_id, t.created_at, t.updated_at,
                       u.username AS lead_username, u.full_name AS lead_full_name,
                       (SELECT COUNT(*) FROM team_members tm2 WHERE tm2.team_id = t.id) AS member_count
                FROM teams t
                LEFT JOIN users u ON u.id = t.lead_user_id
                JOIN team_members tm ON tm.team_id = t.id AND tm.user_id = %s
                ORDER BY t.team_name
                """,
                (user_id,),
            )
        return cur.fetchall()


def update_team(conn, team_id: int, fields: dict) -> None:
    if not fields:
        return
    sets = ", ".join(f"{k} = %s" for k in fields)
    sets += ", updated_at = now()"
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE teams SET {sets} WHERE id = %s",
            list(fields.values()) + [team_id],
        )


def delete_team(conn, team_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM teams WHERE id = %s", (team_id,))


def get_team_members(conn, team_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.id, u.username, u.email, u.full_name, u.status, tm.assigned_at,
                   COALESCE(array_agg(DISTINCT r.role_name) FILTER (WHERE r.role_name IS NOT NULL), '{}') AS roles
            FROM team_members tm
            JOIN users u ON u.id = tm.user_id
            LEFT JOIN user_roles ur ON ur.user_id = u.id
            LEFT JOIN roles r ON r.id = ur.role_id
            WHERE tm.team_id = %s
            GROUP BY u.id, tm.assigned_at
            ORDER BY u.username
            """,
            (team_id,),
        )
        return cur.fetchall()


def is_member(conn, team_id: int, user_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM team_members WHERE team_id = %s AND user_id = %s",
            (team_id, user_id),
        )
        return cur.fetchone() is not None


def add_member(conn, team_id: int, user_id: int) -> bool:
    """Returns True if inserted, False if already a member."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO team_members (team_id, user_id)
            VALUES (%s, %s)
            ON CONFLICT (team_id, user_id) DO NOTHING
            RETURNING user_id
            """,
            (team_id, user_id),
        )
        return cur.fetchone() is not None


def remove_member(conn, team_id: int, user_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM team_members WHERE team_id = %s AND user_id = %s",
            (team_id, user_id),
        )
        return cur.rowcount > 0


def user_team_ids(conn, user_id: int):
    with conn.cursor() as cur:
        cur.execute("SELECT team_id FROM team_members WHERE user_id = %s", (user_id,))
        return [r["team_id"] for r in cur.fetchall()]


def teams_led_by(conn, user_id: int):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM teams WHERE lead_user_id = %s", (user_id,))
        return [r["id"] for r in cur.fetchall()]


def team_member_user_ids(conn, team_ids: list[int]):
    if not team_ids:
        return []
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT user_id FROM team_members WHERE team_id = ANY(%s)",
            (team_ids,),
        )
        return [r["user_id"] for r in cur.fetchall()]
