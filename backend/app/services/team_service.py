from fastapi import HTTPException, status

from ..dependencies import CurrentUser
from ..repositories import team_repo, user_repo
from . import audit_service


def _can_manage_team(user: CurrentUser, team) -> bool:
    """Admin can manage all teams; team lead can manage teams they lead."""
    if user.is_admin:
        return True
    return "team_lead" in user.roles and team["lead_user_id"] == user.id


def _serialize_team(row, include_members=False, conn=None) -> dict:
    data = {
        "id": row["id"],
        "team_name": row["team_name"],
        "description": row["description"],
        "lead_user_id": row["lead_user_id"],
        "lead_username": row.get("lead_username"),
        "lead_full_name": row.get("lead_full_name"),
        "member_count": int(row["member_count"]) if row.get("member_count") is not None else None,
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }
    if include_members and conn is not None:
        data["members"] = [
            {
                "id": m["id"],
                "username": m["username"],
                "email": m["email"],
                "full_name": m["full_name"],
                "status": m["status"],
                "roles": list(m["roles"]) if m.get("roles") else [],
                "assigned_at": m["assigned_at"].isoformat() if m.get("assigned_at") else None,
            }
            for m in team_repo.get_team_members(conn, row["id"])
        ]
    return data


def list_teams(conn, user: CurrentUser):
    is_admin = user.is_admin
    is_lead = "team_lead" in user.roles
    rows = team_repo.list_teams_for_user(conn, user.id, is_admin, is_lead)
    return [_serialize_team(r) for r in rows]


def get_team(conn, team_id: int, user: CurrentUser):
    team = team_repo.get_team(conn, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    # Analysts can only view teams they belong to; leads teams they lead/belong; admin all.
    if not user.is_admin:
        is_lead = "team_lead" in user.roles
        allowed = team_repo.is_member(conn, team_id, user.id) or (
            is_lead and team["lead_user_id"] == user.id
        )
        if not allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this team")
    members = team_repo.get_team_members(conn, team_id)
    data = _serialize_team(team, include_members=False)
    data["members"] = [
        {
            "id": m["id"], "username": m["username"], "email": m["email"],
            "full_name": m["full_name"], "status": m["status"],
            "roles": list(m["roles"]) if m.get("roles") else [],
            "assigned_at": m["assigned_at"].isoformat() if m.get("assigned_at") else None,
        }
        for m in members
    ]
    data["member_count"] = len(members)
    return data


def create_team(conn, data, actor: CurrentUser, ip: str | None):
    if data.lead_user_id is not None and not user_repo.user_exists(conn, data.lead_user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lead user does not exist")
    try:
        team_id = team_repo.create_team(conn, data.team_name, data.description, data.lead_user_id)
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team name already exists")
        raise
    audit_service.log(
        conn, actor_user_id=actor.id, action="team.create", target_type="team",
        target_id=team_id, details={"team_name": data.team_name, "lead_user_id": data.lead_user_id},
        ip_address=ip,
    )
    conn.commit()
    return get_team(conn, team_id, actor)


def update_team(conn, team_id: int, data, actor: CurrentUser, ip: str | None):
    team = team_repo.get_team(conn, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if not _can_manage_team(actor, team):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot update this team")

    fields = {}
    payload = data.model_dump(exclude_unset=True)
    if "team_name" in payload and payload["team_name"] is not None:
        fields["team_name"] = payload["team_name"]
    if "description" in payload:
        fields["description"] = payload["description"]
    if "lead_user_id" in payload:
        if payload["lead_user_id"] is not None and not user_repo.user_exists(conn, payload["lead_user_id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lead user does not exist")
        fields["lead_user_id"] = payload["lead_user_id"]
    if not fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    try:
        team_repo.update_team(conn, team_id, fields)
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team name already exists")
        raise
    audit_service.log(
        conn, actor_user_id=actor.id, action="team.update", target_type="team",
        target_id=team_id, details={"fields": list(fields.keys())}, ip_address=ip,
    )
    conn.commit()
    return get_team(conn, team_id, actor)


def delete_team(conn, team_id: int, actor: CurrentUser, ip: str | None):
    team = team_repo.get_team(conn, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if not actor.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can delete teams")
    team_repo.delete_team(conn, team_id)
    audit_service.log(
        conn, actor_user_id=actor.id, action="team.delete", target_type="team",
        target_id=team_id, details={"team_name": team["team_name"]}, ip_address=ip,
    )
    conn.commit()
    return {"message": "Team deleted"}


def candidate_users(conn, team_id: int, actor: CurrentUser):
    """Active users eligible to join a team (not already members).

    Requires teams.manage_members and manage rights over the specific team.
    """
    team = team_repo.get_team(conn, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if not _can_manage_team(actor, team):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot manage this team")
    with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM team_members WHERE team_id = %s", (team_id,))
        member_ids = [r["user_id"] for r in cur.fetchall()]
    rows = user_repo.list_active_users_excluding(conn, member_ids)
    return [
        {"id": r["id"], "username": r["username"], "email": r["email"],
         "full_name": r["full_name"], "status": r["status"]}
        for r in rows
    ]


def add_member(conn, team_id: int, user_id: int, actor: CurrentUser, ip: str | None):
    team = team_repo.get_team(conn, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if not _can_manage_team(actor, team):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot manage this team")
    member = user_repo.get_user_by_id(conn, user_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if member["status"] != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot add an inactive user to a team")
    if team_repo.is_member(conn, team_id, user_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member of this team")
    team_repo.add_member(conn, team_id, user_id)
    audit_service.log(
        conn, actor_user_id=actor.id, action="team.member_add", target_type="team",
        target_id=team_id, details={"user_id": user_id, "username": member["username"]}, ip_address=ip,
    )
    conn.commit()
    return get_team(conn, team_id, actor)


def remove_member(conn, team_id: int, user_id: int, actor: CurrentUser, ip: str | None):
    team = team_repo.get_team(conn, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if not _can_manage_team(actor, team):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot manage this team")
    if not team_repo.is_member(conn, team_id, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not a member of this team")
    team_repo.remove_member(conn, team_id, user_id)
    audit_service.log(
        conn, actor_user_id=actor.id, action="team.member_remove", target_type="team",
        target_id=team_id, details={"user_id": user_id}, ip_address=ip,
    )
    conn.commit()
    return get_team(conn, team_id, actor)
