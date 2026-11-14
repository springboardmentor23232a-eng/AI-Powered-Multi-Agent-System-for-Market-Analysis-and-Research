from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserPreference
from app.schemas import PreferenceOut, PreferenceUpdate
from app.auth import get_current_user

router = APIRouter(prefix="/preferences", tags=["User Preferences"])

@router.get("", response_model=PreferenceOut)
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve market and analysis period preferences for the authenticated user."""
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    if not prefs:
        # Fallback creation if not yet initialized
        prefs = UserPreference(user_id=current_user.user_id, market="NASDAQ", analysis_period="1 Year")
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.put("", response_model=PreferenceOut)
def update_user_preferences(
    prefs_in: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update preferred market (NSE, BSE, NASDAQ, NYSE) and analysis period (1M to 5Y)."""
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    if not prefs:
        prefs = UserPreference(
            user_id=current_user.user_id,
            market=prefs_in.market,
            analysis_period=prefs_in.analysis_period
        )
        db.add(prefs)
    else:
        prefs.market = prefs_in.market
        prefs.analysis_period = prefs_in.analysis_period

    db.commit()
    db.refresh(prefs)
    return prefs
