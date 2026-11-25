from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User, UserPreference
from ..schemas import PreferenceIO

router = APIRouter(prefix="/preferences", tags=["preferences"])
DEFAULT = PreferenceIO(market="NSE", analysis_period="1y")


@router.get("", response_model=PreferenceIO)
def get_pref(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pref = db.get(UserPreference, user.user_id)
    return pref or DEFAULT


@router.put("", response_model=PreferenceIO)
def save_pref(data: PreferenceIO, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    pref = db.get(UserPreference, user.user_id)
    if pref is None:
        pref = UserPreference(user_id=user.user_id)
        db.add(pref)
    pref.market = data.market
    pref.analysis_period = data.analysis_period
    db.commit()
    return pref