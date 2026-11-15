"""User preferences endpoints."""

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas import PreferencesOut, PreferencesUpdate
from app.services import user_service

router = APIRouter(prefix="/users/me", tags=["preferences"])


@router.get("/preferences", response_model=PreferencesOut)
def read_preferences(current_user: CurrentUser, db: DbSession):
    return user_service.get_or_create_preferences(db, current_user)


@router.put("/preferences", response_model=PreferencesOut)
def update_preferences(changes: PreferencesUpdate, current_user: CurrentUser, db: DbSession):
    return user_service.update_preferences(db, current_user, changes)
