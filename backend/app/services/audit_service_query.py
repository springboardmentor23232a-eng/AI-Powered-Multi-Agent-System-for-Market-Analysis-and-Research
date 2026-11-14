from datetime import datetime, timedelta, timezone

from ..dependencies import CurrentUser
from ..repositories import audit_repo, team_repo, user_repo


def _scoped_actor_ids(conn, user: CurrentUser):
    """Team leads may only view audit events of members in teams they lead (plus themselves)."""
    if user.is_admin:
        return None  # no restriction
    led = team_repo.teams_led_by(conn, user.id)
    member_ids = team_repo.team_member_user_ids(conn, led)
    ids = set(member_ids) | {user.id}
    return list(ids)


def query_logs(conn, user: CurrentUser, actor_user_id, action, status_filter,
               target_type, date_from, date_to, page, page_size):
    allowed = _scoped_actor_ids(conn, user)
    rows, total = audit_repo.query_logs(
        conn,
        actor_user_id=actor_user_id,
        action=action,
        status_filter=status_filter,
        target_type=target_type,
        date_from=date_from,
        date_to=date_to,
        allowed_actor_ids=allowed,
        page=page,
        page_size=page_size,
    )
    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "actor_user_id": r["actor_user_id"],
            "actor_username": r["actor_username"],
            "actor_full_name": r["actor_full_name"],
            "action": r["action"],
            "target_type": r["target_type"],
            "target_id": r["target_id"],
            "status": r["status"],
            "details": r["details"],
            "ip_address": r["ip_address"],
            "timestamp": r["timestamp"].isoformat() if r["timestamp"] else None,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}
