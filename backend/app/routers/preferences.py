from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, UserPreference
from app.schemas import PreferencesIn, PreferencesOut

router = APIRouter(prefix="/preferences", tags=["Preferences"])

def get_or_create(db: Session, user: User):
    pref = db.query(UserPreference).filter_by(user_id=user.id).first()
    if not pref:
        pref = UserPreference(user_id=user.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref

@router.get("", response_model=PreferencesOut)
def get_preferences(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = get_or_create(db, user)
    return PreferencesOut(default_market=p.default_market, default_analysis_period=p.default_analysis_period, updated_at=p.updated_at)

@router.put("", response_model=PreferencesOut)
def update_preferences(payload: PreferencesIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = get_or_create(db, user)
    p.default_market = payload.default_market
    p.default_analysis_period = payload.default_analysis_period
    db.commit()
    db.refresh(p)
    return PreferencesOut(default_market=p.default_market, default_analysis_period=p.default_analysis_period, updated_at=p.updated_at)
