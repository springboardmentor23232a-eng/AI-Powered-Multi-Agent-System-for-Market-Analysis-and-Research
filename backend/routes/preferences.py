
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import UserPreference
from schemas import (
    UserPreferenceUpdate,
    UserPreferenceResponse
)
from routes.authentication import get_current_user
from models import User


router = APIRouter(
    prefix="/preferences",
    tags=["User Preferences"]
)


@router.get("/", response_model=UserPreferenceResponse)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).first()

    if not preferences:
        preferences = UserPreference(
            user_id=current_user.id,
            market="NSI",
            analysis_period="1y"
        )

        db.add(preferences)
        db.commit()
        db.refresh(preferences)

    return preferences


@router.put("/", response_model=UserPreferenceResponse)
def update_preferences(
    preference_data: UserPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Supported markets
    allowed_markets = {
        "NSI",
        "BSE",
        "NASDAQ",
        "NYSE"
    }

    # Supported analysis periods
    allowed_periods = {
        "1mo",
        "3mo",
        "6mo",
        "1y",
        "5y"
    }

    market = preference_data.market.upper()
    period = preference_data.analysis_period.lower()

    # Validate market
    if market not in allowed_markets:
        raise HTTPException(
            status_code=400,
            detail="Unsupported market selected."
        )

    # Validate analysis period
    if period not in allowed_periods:
        raise HTTPException(
            status_code=400,
            detail="Unsupported analysis period selected."
        )

    # Find existing user preferences
    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).first()

    # Create preferences if they don't exist
    if not preferences:
        preferences = UserPreference(
            user_id=current_user.id,
            market=market,
            analysis_period=period
        )
        db.add(preferences)

    else:
        preferences.market = market
        preferences.analysis_period = period

    db.commit()
    db.refresh(preferences)

    return preferences
