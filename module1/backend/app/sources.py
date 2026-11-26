"""Records every data retrieval in `source_documents` (what, where from, when, how clean)."""
from sqlalchemy.orm import Session

from .catalog import Stock
from .market_data import Fetched
from .models import SourceDocument


def record_source(db: Session, stock: Stock, doc_type: str, fetched: Fetched, *, user_id: int | None = None,
                  task_id: int | None = None, record_count: int | None = None,
                  quality: dict | None = None) -> SourceDocument:
    doc = SourceDocument(
        task_id=task_id, user_id=user_id, ticker=stock.ticker, market=stock.market, doc_type=doc_type,
        source_name=fetched.source[:150], source_url=fetched.source_url, is_synthetic=fetched.synthetic,
        retrieved_at=fetched.retrieved_at, record_count=record_count, quality=quality,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc
