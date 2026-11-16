from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.research import (
    ResearchTaskCreate,
    ResearchTaskItemResponse,
    ResearchHistoryResponse,
    ResearchReportResponse,
    ResearchTaskDetailResponse,
)
from app.services.research_service import (
    execute_research_workflow,
    list_user_research_history,
    get_user_research_task_and_report,
)

router = APIRouter(
    prefix="/research",
    tags=["Research History & Workspace"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/tasks",
    response_model=ResearchTaskDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and execute a stock research task",
    description="Initiates research for a ticker symbol, records task state transitions (Pending -> Processing -> Completed), and saves report output in PostgreSQL.",
)
def create_research_task(
    payload: ResearchTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResearchTaskDetailResponse:
    """
    Creates a new research task bound strictly to the authenticated user ID.
    Executes real-time market data retrieval and validates data quality.
    """
    task, report = execute_research_workflow(db=db, user=current_user, request=payload)

    task_item = ResearchTaskItemResponse.model_validate(task)
    task_item.has_report = report is not None

    report_resp = ResearchReportResponse.model_validate(report) if report else None

    return ResearchTaskDetailResponse(
        status="success",
        task=task_item,
        report=report_resp,
    )


@router.get(
    "/history",
    response_model=ResearchHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve authenticated user's research history",
    description="Returns all stock research tasks initiated by the current user, ordered newest first.",
)
def get_user_research_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResearchHistoryResponse:
    """
    Retrieves user-specific research history. User ID is extracted directly from the verified JWT.
    """
    tasks = list_user_research_history(db=db, user_id=current_user.user_id)
    items = []
    for t in tasks:
        item = ResearchTaskItemResponse.model_validate(t)
        item.has_report = t.report is not None
        items.append(item)

    return ResearchHistoryResponse(
        status="success",
        count=len(items),
        data=items,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=ResearchTaskDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve research task details and saved report",
    description="Fetches a specific research task and its stored report. Returns 404 if the task does not belong to the user.",
)
def get_research_task_detail(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResearchTaskDetailResponse:
    """
    Retrieves a research task and report with ownership validation.
    """
    task, report = get_user_research_task_and_report(db=db, task_id=task_id, user_id=current_user.user_id)

    task_item = ResearchTaskItemResponse.model_validate(task)
    task_item.has_report = report is not None

    report_resp = ResearchReportResponse.model_validate(report) if report else None

    return ResearchTaskDetailResponse(
        status="success",
        task=task_item,
        report=report_resp,
    )

