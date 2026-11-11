from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database import get_db
from app.models.preference import UserPreference
from app.models.user import User
from app.schemas.preference import PreferenceResponse, PreferenceUpdateRequest
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/preferences", tags=["Preferences"])


@router.get("", response_model=PreferenceResponse)
def get_user_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve saved preferences for the authenticated user."""
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    if not pref:
        # Create default preferences if none exist
        pref = UserPreference(
            user_id=current_user.user_id,
            preferred_market=settings.DEFAULT_MARKET,
            analysis_period=settings.DEFAULT_ANALYSIS_PERIOD
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.put("", response_model=PreferenceResponse)
def update_user_preferences(
    req: PreferenceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update preferred market and analysis period for the authenticated user."""
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    if not pref:
        pref = UserPreference(
            user_id=current_user.user_id,
            preferred_market=req.preferred_market,
            analysis_period=req.analysis_period
        )
        db.add(pref)
    else:
        pref.preferred_market = req.preferred_market
        pref.analysis_period = req.analysis_period

    db.commit()
    db.refresh(pref)
    return pref

