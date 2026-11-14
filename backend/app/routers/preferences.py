from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, UserPreference
from ..schemas import PreferenceIO

router = APIRouter(prefix="/preferences", tags=["preferences"])


def _get_or_create(db: Session, user: User) -> UserPreference:
    pref = db.get(UserPreference, user.user_id)
    if not pref:
        pref = UserPreference(user_id=user.user_id, market="NASDAQ", analysis_period="1Y")
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.get("", response_model=PreferenceIO)
def read_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_or_create(db, user)


@router.put("", response_model=PreferenceIO)
def update_preferences(data: PreferenceIO, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pref = _get_or_create(db, user)
    pref.market = data.market
    pref.analysis_period = data.analysis_period
    db.commit()
    return pref
