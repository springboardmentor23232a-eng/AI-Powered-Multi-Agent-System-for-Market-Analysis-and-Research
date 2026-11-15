
from fastapi import APIRouter, Depends, status, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
from models import ResearchTask, User
from schemas import (
    ResearchTaskCreate,
    ResearchTaskResponse,
    ResearchTaskUpdate
)

from routes.authentication import get_current_user

from services.stock_data_service import collect_stock_data

from services.financial_analysis_service import (
    analyze_stock_data,
    generate_research_report
)


router = APIRouter(
    prefix="/research",
    tags=["Research History"]
)


# Background research processing function
def mark_task_processing(research_id: int):
    db = SessionLocal()

    try:
        task = (
            db.query(ResearchTask)
            .filter(ResearchTask.research_id == research_id)
            .first()
        )

        if not task:
            return

        # Step 1: Update status to Processing
        task.status = "Processing"
        db.commit()

        # Step 2: Collect stock market data
        stock_data = collect_stock_data(
            task.ticker,
            task.market,
            task.analysis_period
        )

        # Step 3: Calculate financial metrics
        analysis = analyze_stock_data(stock_data)

        # Step 4: Generate research report
        report = generate_research_report(analysis)

        # Step 5: Save report in database
        task.report_content = report
        task.status = "Completed"

        db.commit()

        print(f"Research completed for {task.ticker}")
        print("Financial analysis and report saved successfully.")

    except Exception as error:
        db.rollback()

        task = (
            db.query(ResearchTask)
            .filter(ResearchTask.research_id == research_id)
            .first()
        )

        if task:
            task.status = "Failed"
            db.commit()

        print(f"Research processing error: {error}")

    finally:
        db.close()


# Create a new research task
@router.post(
    "/tasks",
    response_model=ResearchTaskResponse,
    status_code=status.HTTP_201_CREATED
)
def create_research_task(
    task_data: ResearchTaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_task = ResearchTask(
        user_id=current_user.id,
        company_name=task_data.company_name,
        ticker=task_data.ticker.upper(),
        market=task_data.market,
        analysis_period=task_data.analysis_period,
        status="Pending"
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    background_tasks.add_task(
        mark_task_processing,
        new_task.research_id
    )

    return new_task


# Get research history of the logged-in user
@router.get(
    "/tasks",
    response_model=list[ResearchTaskResponse]
)
def get_research_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    research_tasks = (
        db.query(ResearchTask)
        .filter(ResearchTask.user_id == current_user.id)
        .order_by(ResearchTask.research_date.desc())
        .all()
    )

    return research_tasks


# Update research task status and report
@router.patch(
    "/tasks/{research_id}",
    response_model=ResearchTaskResponse
)
def update_research_task(
    research_id: int,
    task_data: ResearchTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = (
        db.query(ResearchTask)
        .filter(
            ResearchTask.research_id == research_id,
            ResearchTask.user_id == current_user.id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Research task not found"
        )

    allowed_statuses = [
        "Pending",
        "Processing",
        "Completed",
        "Failed"
    ]

    if task_data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid research status"
        )

    task.status = task_data.status

    if task_data.report_content is not None:
        task.report_content = task_data.report_content

    db.commit()
    db.refresh(task)

    return task

# Delete a research task
@router.delete(
    "/tasks/{research_id}",
    status_code=status.HTTP_200_OK
)
def delete_research_task(
    research_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = (
        db.query(ResearchTask)
        .filter(
            ResearchTask.research_id == research_id,
            ResearchTask.user_id == current_user.id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Research task not found"
        )

    db.delete(task)
    db.commit()

    return {
        "message": "Research task deleted successfully"
    }

# Delete all research history of the logged-in user
@router.delete(
    "/tasks",
    status_code=status.HTTP_200_OK
)
def delete_all_research_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted_count = (
        db.query(ResearchTask)
        .filter(ResearchTask.user_id == current_user.id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return {
        "message": "All research history deleted successfully",
        "deleted_count": deleted_count
    }