from datetime import datetime, timedelta, timezone

from ..dependencies import CurrentUser
from ..repositories import audit_repo, team_repo, user_repo


def get_stats(conn, user: CurrentUser) -> dict:
    with conn.cursor() as cur:
        if user.is_admin:
            cur.execute("SELECT COUNT(*) AS c FROM users")
            total_users = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM users WHERE status = 'active'")
            active_users = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM teams")
            total_teams = cur.fetchone()["c"]
            cur.execute(
                "SELECT COUNT(*) AS c FROM audit_logs WHERE timestamp >= now() - interval '24 hours'"
            )
            events_24h = cur.fetchone()["c"]
            cur.execute(
                "SELECT COUNT(*) AS c FROM audit_logs WHERE status = 'failure' AND timestamp >= now() - interval '24 hours'"
            )
            failures_24h = cur.fetchone()["c"]
            scope = "all"
        elif "team_lead" in user.roles:
            led = team_repo.teams_led_by(conn, user.id)
            member_ids = team_repo.team_member_user_ids(conn, led)
            ids = list(set(member_ids) | {user.id})
            cur.execute("SELECT COUNT(*) AS c FROM users WHERE id = ANY(%s)", (ids,))
            total_users = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM users WHERE id = ANY(%s) AND status = 'active'", (ids,))
            active_users = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM teams WHERE id = ANY(%s)", (led,))
            total_teams = cur.fetchone()["c"]
            cur.execute(
                "SELECT COUNT(*) AS c FROM audit_logs WHERE actor_user_id = ANY(%s) AND timestamp >= now() - interval '24 hours'",
                (ids,),
            )
            events_24h = cur.fetchone()["c"]
            cur.execute(
                "SELECT COUNT(*) AS c FROM audit_logs WHERE actor_user_id = ANY(%s) AND status = 'failure' AND timestamp >= now() - interval '24 hours'",
                (ids,),
            )
            failures_24h = cur.fetchone()["c"]
            scope = "team"
        else:
            team_ids = team_repo.user_team_ids(conn, user.id)
            cur.execute("SELECT COUNT(*) AS c FROM team_members WHERE team_id = ANY(%s)", (team_ids,))
            team_size = cur.fetchone()["c"]
            cur.execute(
                "SELECT COUNT(*) AS c FROM audit_logs WHERE actor_user_id = %s AND timestamp >= now() - interval '24 hours'",
                (user.id,),
            )
            events_24h = cur.fetchone()["c"]
            total_users = team_size
            active_users = team_size
            total_teams = len(team_ids)
            failures_24h = 0
            scope = "self"

    # Recent audit activity (scoped)
    if user.is_admin:
        allowed = None
    elif "team_lead" in user.roles:
        led = team_repo.teams_led_by(conn, user.id)
        member_ids = team_repo.team_member_user_ids(conn, led)
        allowed = list(set(member_ids) | {user.id})
    else:
        allowed = [user.id]

    rows, _ = audit_repo.query_logs(conn, allowed_actor_ids=allowed, page=1, page_size=5)
    recent = [
        {
            "id": r["id"],
            "actor_username": r["actor_username"],
            "action": r["action"],
            "status": r["status"],
            "timestamp": r["timestamp"].isoformat() if r["timestamp"] else None,
        }
        for r in rows
    ]

    # Role distribution (scoped to visible users)
    with conn.cursor() as cur:
        if user.is_admin:
            cur.execute(
                """
                SELECT r.role_name, COUNT(DISTINCT ur.user_id) AS c
                FROM roles r
                LEFT JOIN user_roles ur ON ur.role_id = r.id
                GROUP BY r.role_name ORDER BY c DESC
                """
            )
        elif allowed is not None:
            cur.execute(
                """
                SELECT r.role_name, COUNT(DISTINCT ur.user_id) AS c
                FROM roles r
                LEFT JOIN user_roles ur ON ur.role_id = r.id AND ur.user_id = ANY(%s)
                GROUP BY r.role_name ORDER BY c DESC
                """,
                (allowed,),
            )
        role_distribution = [{"role": r["role_name"], "count": r["c"]} for r in cur.fetchall()]

        # Audit events by action, last 7 days (scoped)
        if allowed is None:
            cur.execute(
                """
                SELECT action, COUNT(*) AS c FROM audit_logs
                WHERE timestamp >= now() - interval '7 days'
                GROUP BY action ORDER BY c DESC LIMIT 8
                """
            )
        else:
            cur.execute(
                """
                SELECT action, COUNT(*) AS c FROM audit_logs
                WHERE timestamp >= now() - interval '7 days' AND actor_user_id = ANY(%s)
                GROUP BY action ORDER BY c DESC LIMIT 8
                """,
                (allowed,),
            )
        events_by_action = [{"action": r["action"], "count": r["c"]} for r in cur.fetchall()]

    return {
        "scope": scope,
        "total_users": total_users,
        "active_users": active_users,
        "total_teams": total_teams,
        "events_24h": events_24h,
        "failures_24h": failures_24h,
        "recent_activity": recent,
        "role_distribution": role_distribution,
        "events_by_action": events_by_action,
    }
