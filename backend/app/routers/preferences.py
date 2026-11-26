from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..catalog import MARKET_INFO, PERIOD_INFO
from ..database import get_db
from ..deps import get_current_user
from ..models import User, UserPreference
from ..schemas import PreferencesIn, PreferencesOut

router = APIRouter(prefix="/api", tags=["preferences"])


def get_or_create_prefs(db: Session, user: User) -> UserPreference:
    prefs = db.get(UserPreference, user.user_id)
    if prefs is None:
        prefs = UserPreference(user_id=user.user_id, market="NASDAQ", analysis_period="1Y")
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.get("/options")
def options(_: User = Depends(get_current_user)):
    """Dropdown contents for the frontend."""
    return {
        "markets": [{"code": c, "name": i["name"], "example": i["example"]} for c, i in MARKET_INFO.items()],
        "periods": [{"code": c, "label": i["label"]} for c, i in PERIOD_INFO.items()],
    }


@router.get("/preferences", response_model=PreferencesOut)
def read_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_or_create_prefs(db, user)


@router.put("/preferences", response_model=PreferencesOut)
def save_preferences(body: PreferencesIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prefs = get_or_create_prefs(db, user)
    prefs.market, prefs.analysis_period = body.market, body.analysis_period
    db.commit()
    db.refresh(prefs)
    return prefs
