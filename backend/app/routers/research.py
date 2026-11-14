from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, ResearchTask, UserPreference
from app.schemas import ResearchCreate, ResearchOut

router = APIRouter(prefix="/research", tags=["Research history"])

@router.post("", response_model=ResearchOut, status_code=201)
@router.post("/start", response_model=ResearchOut, status_code=201)
def create_research(payload: ResearchCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    preference = db.query(UserPreference).filter_by(user_id=user.id).first()
    market = payload.market or (preference.default_market if preference else "NASDAQ")
    analysis_period = payload.analysis_period or (preference.default_analysis_period if preference else "1 Year")
    task = ResearchTask(user_id=user.id, company_name=payload.company_name.strip(), ticker=payload.ticker.strip().upper(), market=market, analysis_period=analysis_period, status="pending")
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get("/history", response_model=list[ResearchOut])
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ResearchTask).filter(ResearchTask.user_id == user.id).order_by(ResearchTask.created_at.desc()).all()

@router.get("/{task_id}", response_model=ResearchOut)
def get_task(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id, ResearchTask.user_id == user.id).first()
    if not task:
        raise HTTPException(404, "Research task not found.")
    return task

@router.get("/{task_id}/report")
def get_report(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id, ResearchTask.user_id == user.id).first()
    if not task:
        raise HTTPException(404, "Research task not found.")
    if not task.report:
        raise HTTPException(404, "A report is not available yet. The research workflow has not been connected in this milestone.")
    return task.report.report_content
