import logging
from datetime import datetime
from typing import List, Optional
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.research import ResearchReport, ResearchSession
from app.models.user import User
from app.schemas.analytics import WorkspaceSummaryResponse
from app.schemas.auth import MessageResponse
from app.schemas.comparison import ComparisonRequest, ComparisonResponse
from app.schemas.research import (
    ResearchCreateRequest,
    ResearchReportResponse,
    ResearchSessionDetailResponse,
    ResearchSessionListResponse,
    ResearchSessionResponse,
)
from app.services.comparative_analysis import ComparativeAnalysisService
from app.services.report_exporter import ReportExporter
from app.services.research_orchestrator import (
    ResearchOrchestrator,
    run_research_background,
)
from app.services.workspace_analytics import WorkspaceAnalyticsService

logger = logging.getLogger("fincrew.research_router")

router = APIRouter(
    prefix="/api/research",
    tags=["Research"],
)


@router.post(
    "/analyze",
    response_model=ResearchSessionDetailResponse,
    summary="Initiate Stock Equity Research Analysis",
    description=(
        "Initiates an end-to-end multi-agent equity research session for a given ticker. "
        "By default, dispatches the analysis to a background worker and returns HTTP 202 Accepted. "
        "If run_sync=true is specified, executes synchronously and returns the completed report."
    ),
)
def analyze_stock(
    payload: ResearchCreateRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    run_sync: bool = Query(
        False,
        description="If true, executes research synchronously in the request thread.",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Create session record
    session = ResearchSession(
        user_id=current_user.id,
        ticker=payload.ticker,
        status="PENDING",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # 2. Synchronous execution (useful for testing and immediate reporting)
    if run_sync:
        orchestrator = ResearchOrchestrator()
        orchestrator.run(session_id=session.id, db=db)
        db.refresh(session)
        response.status_code = status.HTTP_200_OK
        return session

    # 3. Asynchronous execution via BackgroundTasks (default)
    background_tasks.add_task(run_research_background, session.id)
    response.status_code = status.HTTP_202_ACCEPTED
    return session


@router.post(
    "/sessions",
    response_model=ResearchSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Research Session Record",
    description="Creates a new research session record in PENDING status without immediately triggering execution.",
)
def create_research_session(
    payload: ResearchCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = ResearchSession(
        user_id=current_user.id,
        ticker=payload.ticker,
        status="PENDING",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post(
    "/sessions/{session_id}/start",
    response_model=ResearchSessionDetailResponse,
    summary="Start Research for an Existing Session",
    description="Triggers the multi-agent pipeline on an existing pending or failed session.",
)
def start_research_session(
    session_id: int,
    response: Response,
    background_tasks: BackgroundTasks,
    run_sync: bool = Query(False, description="If true, executes synchronously."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session with ID {session_id} not found.",
        )

    # Enforce strict user ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not own this research session.",
        )

    if session.status == "IN_PROGRESS":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Research pipeline is already currently in progress for this session.",
        )

    if run_sync:
        orchestrator = ResearchOrchestrator()
        orchestrator.run(session_id=session.id, db=db)
        db.refresh(session)
        response.status_code = status.HTTP_200_OK
        return session

    session.status = "PENDING"
    db.commit()
    background_tasks.add_task(run_research_background, session.id)
    response.status_code = status.HTTP_202_ACCEPTED
    return session


@router.get(
    "/sessions",
    response_model=ResearchSessionListResponse,
    summary="List Previous Research Sessions",
    description="Retrieves previous stock research sessions initiated by the authenticated user, sorted latest first.",
)
def list_user_research_sessions(
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(ResearchSession)
        .filter(ResearchSession.user_id == current_user.id)
        .order_by(ResearchSession.created_at.desc())
    )
    total = query.count()
    sessions = query.offset(offset).limit(limit).all()

    return ResearchSessionListResponse(total=total, sessions=sessions)


@router.get(
    "/sessions/{session_id}",
    response_model=ResearchSessionDetailResponse,
    summary="Get Research Session Status and Report",
    description="Fetches current status, metadata, and attached research report for a specific session.",
)
def get_research_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session with ID {session_id} not found.",
        )

    # Enforce strict user ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not own this research session.",
        )

    return session


@router.get(
    "/sessions/{session_id}/report",
    response_model=ResearchReportResponse,
    summary="Retrieve Completed Research Report",
    description="Retrieves the synthesized research report once analysis is completed.",
)
def get_research_report(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session with ID {session_id} not found.",
        )

    # Enforce strict user ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not own this research session.",
        )

    if session.status == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Research analysis failed: {session.error_message}",
        )

    if session.status in ("PENDING", "IN_PROGRESS"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Research is still in progress (Current status: {session.status}). Please check back shortly.",
        )

    if not session.report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research report not found for this completed session.",
        )

    return session.report


@router.get(
    "/sessions/{session_id}/export",
    summary="Export Completed Research Report",
    description="Exports a synthesized research report in Markdown, JSON, HTML, or genuine binary PDF format.",
)
def export_research_report(
    session_id: int,
    format: str = Query(
        "markdown",
        pattern="^(markdown|json|html|pdf)$",
        description="Target export format: markdown, json, html, or pdf.",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session with ID {session_id} not found.",
        )

    # Enforce strict user ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not own this research session.",
        )

    if session.status != "COMPLETED" or not session.report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot export research session in status '{session.status}'. Only COMPLETED reports can be exported.",
        )

    report = session.report
    ticker = report.ticker
    timestamp_str = datetime.now().strftime("%Y%m%d")

    if format == "json":
        data = ReportExporter.export_json(report)
        return JSONResponse(
            content=data,
            headers={
                "Content-Disposition": f'attachment; filename="{ticker}_report_{timestamp_str}.json"'
            },
        )
    elif format == "html":
        html_content = ReportExporter.export_html(report)
        return HTMLResponse(
            content=html_content,
            headers={
                "Content-Disposition": f'inline; filename="{ticker}_report_{timestamp_str}.html"'
            },
        )
    elif format == "pdf":
        pdf_bytes = ReportExporter.export_pdf(report)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{ticker}_report_{timestamp_str}.pdf"'
            },
        )
    else:  # markdown
        md_content = ReportExporter.export_markdown(report)
        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{ticker}_report_{timestamp_str}.md"'
            },
        )


@router.delete(
    "/sessions/{session_id}",
    response_model=MessageResponse,
    summary="Delete Research Session",
    description="Permanently deletes a research session and its associated report. Only the session owner can delete.",
)
def delete_research_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session with ID {session_id} not found.",
        )

    # Enforce strict user ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not own this research session.",
        )

    ticker = session.ticker
    db.delete(session)
    db.commit()

    logger.info("Deleted research session %d (%s) for user %d", session_id, ticker, current_user.id)
    return MessageResponse(
        message=f"Research session {session_id} for ticker {ticker} deleted successfully."
    )


@router.post(
    "/compare",
    response_model=ComparisonResponse,
    summary="Multi-Stock Comparative Analysis",
    description="Compares 2 to 5 completed research sessions side-by-side across fundamental, technical, sentiment, risk, and consensus metrics.",
)
def compare_stocks(
    payload: ComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComparativeAnalysisService.compare_sessions(
        session_ids=payload.session_ids,
        user_id=current_user.id,
        db=db,
    )


@router.get(
    "/analytics/summary",
    response_model=WorkspaceSummaryResponse,
    summary="Get Workspace Research Analytics Summary",
    description="Returns aggregate research analytics, recommendation distributions, confidence scores, and sector exposures for the authenticated user.",
)
def get_workspace_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return WorkspaceAnalyticsService.get_user_summary(
        user_id=current_user.id,
        db=db,
    )

