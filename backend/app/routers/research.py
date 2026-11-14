from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, ResearchTask
from app.schemas import ResearchTaskCreate, ResearchTaskResponse
from app.auth import get_current_user

router = APIRouter(prefix="/research", tags=["Research Tasks (Module 1 Section 4)"])


@router.get("/history", response_model=List[ResearchTaskResponse])
def get_user_research_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns only the authenticated user's research history tasks
    ordered by creation date descending.
    """
    tasks = db.query(ResearchTask).filter(
        ResearchTask.user_id == current_user.user_id
    ).order_by(ResearchTask.created_at.desc()).all()
    return tasks


@router.post("/start", response_model=ResearchTaskResponse, status_code=status.HTTP_201_CREATED)
def start_research_task(
    request: ResearchTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new research task for the authenticated user.
    """
    ticker_clean = request.ticker.strip().upper()
    new_task = ResearchTask(
        user_id=current_user.user_id,
        ticker=ticker_clean,
        market=request.market,
        requested_period=request.requested_period,
        status="Completed"  # Marked completed for Module 1 demonstration
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

