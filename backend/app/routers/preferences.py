from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserPreference
from app.schemas import UserPreferenceUpdate, UserPreferenceResponse
from app.auth import get_current_user

router = APIRouter(prefix="/preferences", tags=["User Preferences"])


@router.get("", response_model=UserPreferenceResponse)
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the user's saved market and timeframe preferences.
    If none exist, seeds default preferences (NSE, 1 Year).
    """
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    if not pref:
        pref = UserPreference(
            user_id=current_user.user_id,
            market="NSE",
            analysis_period="1 Year"
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.put("", response_model=UserPreferenceResponse)
def update_user_preferences(
    update_data: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the market and analysis period preferences for the authenticated user.
    """
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    if not pref:
        pref = UserPreference(
            user_id=current_user.user_id,
            market=update_data.market,
            analysis_period=update_data.analysis_period
        )
        db.add(pref)
    else:
        pref.market = update_data.market
        pref.analysis_period = update_data.analysis_period

    db.commit()
    db.refresh(pref)
    return pref

