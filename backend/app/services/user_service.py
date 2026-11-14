from fastapi import HTTPException, status

from ..dependencies import CurrentUser
from ..repositories import role_repo, user_repo
from ..security import hash_password
from . import audit_service


def serialize_user(row) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "full_name": row["full_name"],
        "status": row["status"],
        "roles": list(row["roles"]) if row.get("roles") else [],
        "role_ids": [int(x) for x in row["role_ids"]] if row.get("role_ids") else [],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


def list_users(conn, search, status_filter, page, page_size):
    rows, total = user_repo.list_users(conn, search, status_filter, page, page_size)
    return {
        "items": [serialize_user(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_user(conn, user_id: int):
    row = user_repo.get_user_by_id(conn, user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    roles = user_repo.get_user_roles(conn, user_id)
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "full_name": row["full_name"],
        "status": row["status"],
        "roles": [{"id": r["id"], "role_name": r["role_name"], "description": r["description"]} for r in roles],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
    }


def create_user(conn, data, actor: CurrentUser, ip: str | None):
    if not role_repo.valid_role_ids(conn, data.role_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more role IDs are invalid")
    try:
        user_id = user_repo.create_user(
            conn, data.username, data.email, data.full_name, hash_password(data.password)
        )
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already exists")
        raise
    if data.role_ids:
        user_repo.replace_user_roles(conn, user_id, data.role_ids)
    audit_service.log(
        conn, actor_user_id=actor.id, action="user.create", target_type="user",
        target_id=user_id, details={"username": data.username, "email": data.email,
                                     "role_ids": data.role_ids}, ip_address=ip,
    )
    conn.commit()
    return get_user(conn, user_id)


def update_user(conn, user_id: int, data, actor: CurrentUser, ip: str | None):
    if not user_repo.user_exists(conn, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    fields = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    try:
        user_repo.update_user(conn, user_id, fields)
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already exists")
        raise
    audit_service.log(
        conn, actor_user_id=actor.id, action="user.update", target_type="user",
        target_id=user_id, details={"fields": list(fields.keys())}, ip_address=ip,
    )
    conn.commit()
    return get_user(conn, user_id)


def set_status(conn, user_id: int, new_status: str, actor: CurrentUser, ip: str | None):
    if not user_repo.user_exists(conn, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_id == actor.id and new_status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate your own account")
    user_repo.set_user_status(conn, user_id, new_status)
    if new_status != "active":
        from ..repositories import token_repo
        token_repo.revoke_all_user_tokens(conn, user_id)
    audit_service.log(
        conn, actor_user_id=actor.id,
        action="user.activate" if new_status == "active" else "user.deactivate",
        target_type="user", target_id=user_id, details={"status": new_status}, ip_address=ip,
    )
    conn.commit()
    return get_user(conn, user_id)


def set_roles(conn, user_id: int, role_ids: list[int], actor: CurrentUser, ip: str | None):
    if not user_repo.user_exists(conn, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not role_repo.valid_role_ids(conn, role_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more role IDs are invalid")
    before = [r["role_name"] for r in user_repo.get_user_roles(conn, user_id)]
    user_repo.replace_user_roles(conn, user_id, role_ids)
    after_roles = user_repo.get_user_roles(conn, user_id)
    audit_service.log(
        conn, actor_user_id=actor.id, action="user.roles_change", target_type="user",
        target_id=user_id,
        details={"before": before, "after": [r["role_name"] for r in after_roles]},
        ip_address=ip,
    )
    conn.commit()
    return get_user(conn, user_id)
