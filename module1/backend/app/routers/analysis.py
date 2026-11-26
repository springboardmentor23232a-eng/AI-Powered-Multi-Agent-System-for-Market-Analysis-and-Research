"""Research-agent endpoints (Milestone 2).

GET /api/analysis/{market}/{ticker}/{agent}?period=   agent = fundamental | technical | news | risk | all
GET /api/analysis/dataset                              status of the Kaggle reference dataset (loaded? columns matched?)

Each agent returns its defined structured output (agents/schemas.py). Every data retrieval is logged in source_documents
for the signed-in user. These run the agents on demand; the research-task workflow runs the same agents and stores
their outputs in agent_results.
"""
import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import catalog
from ..agents import AGENT_ORDER, build_context, run_agent
from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..financial_dataset import DATASET_NAME, DATASET_URL, DEFAULT_PATH, get_dataset
from ..market_data import MarketDataError
from ..models import User
from ..schemas import Market, Period

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis agents"])


@router.get("/dataset")
def dataset_status(user: User = Depends(get_current_user)):
    """Is the reference CSV loaded, which columns were recognised, and what is ignored?"""
    base = {"name": DATASET_NAME, "url": DATASET_URL, "expected_path": str(DEFAULT_PATH), "configured_path": settings.financials_dataset_path or None}
    try:
        ds = get_dataset()
    except ValueError as exc:
        return {**base, "loaded": False, "error": str(exc)}
    if ds is None:
        return {**base, "loaded": False, "error": None,
                "how_to_load": "Download the CSV from the Kaggle link, save it as backend/data/financial_statements.csv "
                               "(or set FINANCIALS_DATASET_PATH), then restart the backend."}
    return {**base, "loaded": True, "file": ds.path, "rows": len(ds.rows), "companies": len(ds.companies()),
            "sample_companies": ds.companies()[:10], "matched_columns": ds.column_map, "ignored_columns": ds.unmapped_columns,
            "load_report": ds.report}


@router.get("/{market}/{ticker}/{agent}")
def run_agents(market: Market, ticker: str, agent: Literal["fundamental", "technical", "news", "risk", "all"],
               period: Period = "1Y", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        stock = catalog.validate_research_request(ticker, market, period)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    try:
        ctx = build_context(stock, period, db=db, user_id=user.user_id)
    except (MarketDataError, ValueError) as exc:
        raise HTTPException(502, str(exc))
    wanted = AGENT_ORDER if agent in ("all", "risk") else (agent,)
    done: dict = {}
    for name in AGENT_ORDER:            # risk needs the other three, so they run first
        if name in wanted:
            done[name] = run_agent(name, ctx, done)
    outputs = done if agent == "all" else {agent: done[agent]}
    return {"ticker": stock.ticker, "name": stock.name, "market": stock.market, "period": period,
            "agents": {k: v.model_dump(mode="json") for k, v in outputs.items()}}
