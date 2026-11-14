from fastapi import HTTPException, status

from ..dependencies import CurrentUser
from ..repositories import role_repo
from . import audit_service


def list_roles(conn):
    rows = role_repo.list_roles(conn)
    return [
        {
            "id": r["id"],
            "role_name": r["role_name"],
            "description": r["description"],
            "permissions": list(r["permissions"]) if r.get("permissions") else [],
        }
        for r in rows
    ]


def list_permissions(conn):
    rows = role_repo.list_permissions(conn)
    return [
        {
            "id": r["id"],
            "permission_code": r["permission_code"],
            "module": r["module"],
            "description": r["description"],
        }
        for r in rows
    ]


def get_role_permissions(conn, role_id: int):
    role = role_repo.get_role(conn, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    perms = role_repo.get_role_permissions(conn, role_id)
    return {
        "id": role["id"],
        "role_name": role["role_name"],
        "description": role["description"],
        "permissions": [
            {"id": p["id"], "permission_code": p["permission_code"], "module": p["module"],
             "description": p["description"]}
            for p in perms
        ],
    }


def set_role_permissions(conn, role_id: int, permission_ids: list[int], actor: CurrentUser, ip: str | None):
    role = role_repo.get_role(conn, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role["role_name"] == "administrator":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrator role permissions cannot be modified",
        )
    if not role_repo.valid_permission_ids(conn, permission_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more permission IDs are invalid")
    before = [p["permission_code"] for p in role_repo.get_role_permissions(conn, role_id)]
    role_repo.set_role_permissions(conn, role_id, permission_ids)
    after = [p["permission_code"] for p in role_repo.get_role_permissions(conn, role_id)]
    audit_service.log(
        conn, actor_user_id=actor.id, action="role.permissions_change", target_type="role",
        target_id=role_id, details={"role_name": role["role_name"], "before": before, "after": after},
        ip_address=ip,
    )
    conn.commit()
    return get_role_permissions(conn, role_id)
