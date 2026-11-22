from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..marketdata import get_provider
from ..marketdata.collector import NoUsableData, collect
from ..marketdata.providers.base import ProviderError, SymbolNotFound
from ..models import DataCollection, PriceBar, User, UserPreference
from ..schemas import CollectIn, CollectionDetail, CollectionOut, PriceBarOut, SourceInfo

router = APIRouter(prefix="/market-data", tags=["market-data"])


def _owned(db: Session, user: User, collection_id: int) -> DataCollection:
    stmt = select(DataCollection).where(DataCollection.collection_id == collection_id, DataCollection.user_id == user.user_id)
    col = db.scalar(stmt)
    if not col:
        raise HTTPException(404, "Collection not found")
    return col


@router.get("/source", response_model=SourceInfo)
def source(_: User = Depends(get_current_user)):
    p = get_provider()
    return SourceInfo(name=p.name, kind=p.kind, symbols=p.symbols())


@router.post("/collect", response_model=CollectionOut, status_code=201)
def collect_data(data: CollectIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pref = db.get(UserPreference, user.user_id)
    period = pref.analysis_period if pref else "1Y"
    try:
        return collect(db, get_provider(), user.user_id, data.ticker, data.company_name, data.market, period)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except SymbolNotFound as e:
        raise HTTPException(404, str(e))
    except ProviderError as e:
        raise HTTPException(502, str(e))
    except NoUsableData as e:
        raise HTTPException(422, str(e))


@router.get("", response_model=list[CollectionOut])
def list_collections(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(DataCollection).where(DataCollection.user_id == user.user_id).order_by(DataCollection.retrieved_at.desc())
    return db.scalars(stmt).all()


@router.get("/{collection_id}", response_model=CollectionDetail)
def collection_detail(collection_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _owned(db, user, collection_id)


@router.get("/{collection_id}/prices", response_model=list[PriceBarOut])
def collection_prices(collection_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owned(db, user, collection_id)
    return db.scalars(select(PriceBar).where(PriceBar.collection_id == collection_id).order_by(PriceBar.date)).all()
