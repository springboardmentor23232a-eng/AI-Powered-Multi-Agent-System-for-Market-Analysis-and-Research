from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.preference import (
    PreferenceUpdate,
    PreferenceResponse,
)
from app.services.preference_service import (
    get_or_create_user_preference,
    update_user_preference,
)

router = APIRouter(
    prefix="/preferences",
    tags=["User Preferences"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "",
    response_model=PreferenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current user's preferences",
    description=(
        "Returns the authenticated user's saved market and analysis period preferences. "
        "Initializes and returns default preferences (NSE, 1mo) if the user has no existing record."
    ),
)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferenceResponse:
    """
    Returns user-specific preferences derived strictly from the verified JWT.
    """
    pref = get_or_create_user_preference(db=db, user_id=current_user.user_id)
    return PreferenceResponse.model_validate(pref)


@router.put(
    "",
    response_model=PreferenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user's preferences",
    description=(
        "Updates the authenticated user's market and analysis period preferences. "
        "Validates input against allowed values (NSE, BSE, NASDAQ, NYSE and 1mo, 3mo, 6mo, 1y, 5y). "
        "Returns HTTP 422 for invalid values."
    ),
)
def update_preferences(
    payload: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferenceResponse:
    """
    Updates preferences for the current authenticated user only.
    User ID is extracted securely from current_user.user_id.
    """
    pref = update_user_preference(db=db, user_id=current_user.user_id, request=payload)
    return PreferenceResponse.model_validate(pref)
