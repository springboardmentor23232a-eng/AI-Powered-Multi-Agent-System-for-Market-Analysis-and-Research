from ..repositories import audit_repo


def log(conn, actor_user_id, action, target_type=None, target_id=None,
        status="success", details=None, ip_address=None):
    audit_repo.log_event(
        conn,
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        status=status,
        details=details,
        ip_address=ip_address,
    )
