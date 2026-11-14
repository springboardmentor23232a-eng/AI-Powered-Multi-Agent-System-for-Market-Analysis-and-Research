from fastapi import APIRouter, Depends, Request

from ..dependencies import CurrentUser, get_db, require_permissions
from ..models.schemas import TeamCreate, TeamMemberAdd, TeamUpdate
from ..services import team_service

router = APIRouter(prefix="/teams", tags=["teams"])

VIEW = require_permissions("teams.view")
CREATE = require_permissions("teams.create")
UPDATE = require_permissions("teams.update")
DELETE = require_permissions("teams.delete")
MEMBERS = require_permissions("teams.manage_members")


def _ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("")
def list_teams(user: CurrentUser = Depends(VIEW), conn=Depends(get_db)):
    return team_service.list_teams(conn, user)


@router.post("", status_code=201)
def create_team(
    payload: TeamCreate,
    request: Request,
    user: CurrentUser = Depends(CREATE),
    conn=Depends(get_db),
):
    return team_service.create_team(conn, payload, user, _ip(request))


@router.get("/{team_id}")
def get_team(team_id: int, user: CurrentUser = Depends(VIEW), conn=Depends(get_db)):
    return team_service.get_team(conn, team_id, user)


@router.put("/{team_id}")
def update_team(
    team_id: int,
    payload: TeamUpdate,
    request: Request,
    user: CurrentUser = Depends(UPDATE),
    conn=Depends(get_db),
):
    return team_service.update_team(conn, team_id, payload, user, _ip(request))


@router.delete("/{team_id}")
def delete_team(
    team_id: int,
    request: Request,
    user: CurrentUser = Depends(DELETE),
    conn=Depends(get_db),
):
    return team_service.delete_team(conn, team_id, user, _ip(request))


@router.get("/{team_id}/candidate-users")
def candidate_users(team_id: int, user: CurrentUser = Depends(MEMBERS), conn=Depends(get_db)):
    return team_service.candidate_users(conn, team_id, user)


@router.post("/{team_id}/members", status_code=201)
def add_member(
    team_id: int,
    payload: TeamMemberAdd,
    request: Request,
    user: CurrentUser = Depends(MEMBERS),
    conn=Depends(get_db),
):
    return team_service.add_member(conn, team_id, payload.user_id, user, _ip(request))


@router.delete("/{team_id}/members/{user_id}")
def remove_member(
    team_id: int,
    user_id: int,
    request: Request,
    user: CurrentUser = Depends(MEMBERS),
    conn=Depends(get_db),
):
    return team_service.remove_member(conn, team_id, user_id, user, _ip(request))
