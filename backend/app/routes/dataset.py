import io
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from sqlalchemy.orm import Session
import pandas as pd

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.research_task import ResearchTask, ResearchReport
from app.schemas.dataset import (
    DatasetCollectionRequest,
    DatasetValidationReportResponse,
    DatasetReportsHistoryResponse,
    DatasetReportListItem,
)
from app.services.dataset_providers.registry import ProviderRegistry
from app.services.data_validation_agent import validate_and_process_dataset
from app.services.dataset_ai_agent import synthesize_validation_narrative
from app.services.validation_service import validate_ticker_symbol
from app.services.research_service import determine_market_from_ticker
from app.services.stock_service import get_company_overview

logger = logging.getLogger("uvicorn.error")

router = APIRouter(
    prefix="/dataset",
    tags=["Dataset Collection & Validation Agent"],
    dependencies=[Depends(get_current_user)],
)

provider_registry = ProviderRegistry()


@router.post(
    "/collect-and-validate",
    response_model=DatasetValidationReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute automated stock dataset collection and validation",
    description="Discovers public data sources, ingests historical OHLCV data, creates raw snapshot, executes 10 deterministic validation checks, computes quality score, and synthesizes AI narrative.",
)
def collect_and_validate_dataset(
    payload: DatasetCollectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DatasetValidationReportResponse:
    """
    Automated dataset collection and validation workflow bound strictly to authenticated user.
    """
    clean_ticker = validate_ticker_symbol(payload.ticker)
    market = determine_market_from_ticker(clean_ticker, payload.market)

    # 1. Gracefully resolve company name if available
    company_name = clean_ticker
    try:
        overview = get_company_overview(ticker=clean_ticker)
        company_name = overview.company_name or clean_ticker
    except Exception:
        pass

    # 2. Record initial task in PostgreSQL
    task = ResearchTask(
        user_id=current_user.user_id,
        ticker=clean_ticker,
        company_name=company_name,
        market=market,
        requested_period=payload.period,
        status="Processing",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        # 3. Provider Discovery & Ingestion
        raw_df, active_provider, latency_ms, attempt_logs, retrieved_at = provider_registry.collect_dataset(
            ticker=clean_ticker,
            period=payload.period,
            market=market,
        )

        # 4. Deterministic Validation Engine (Non-overlapping defect hierarchy)
        raw_snap, val_summary, quality_metrics, issues = validate_and_process_dataset(
            raw_input_df=raw_df,
            ticker=clean_ticker,
            data_source=active_provider,
            retrieval_timestamp=retrieved_at,
        )

        # 5. AI Narrative Synthesis Engine (Strict factual boundaries)
        ai_narrative = synthesize_validation_narrative(
            ticker=clean_ticker,
            company_name=company_name,
            market=market,
            active_provider=active_provider,
            quality=quality_metrics,
            val_summary=val_summary,
            raw_snap=raw_snap,
            issues=issues,
        )

        # 6. Finalize Task Status
        task.status = "Completed" if quality_metrics.validation_status != "FAILED" else "Failed"
        task.completed_at = datetime.now(timezone.utc)

        # 7. Build Response Object
        report_data = {
            "ticker": clean_ticker,
            "company_name": company_name,
            "market": market,
            "requested_period": payload.period,
            "active_provider": active_provider,
            "retrieval_timestamp": retrieved_at,
            "latency_ms": latency_ms,
            "validation_status": quality_metrics.validation_status,
            "quality_metrics": quality_metrics.model_dump(),
            "raw_snapshot": raw_snap.model_dump(),
            "validated_summary": val_summary.model_dump(),
            "provider_attempts": [a.model_dump() for a in attempt_logs],
            "issues": [i.model_dump() for i in issues],
            "ai_explanation": ai_narrative.model_dump(),
        }

        # 8. Persist Report in PostgreSQL (Native JSON column, zero migration)
        report = ResearchReport(
            task_id=task.task_id,
            report_content={
                "type": "dataset_validation",
                "validation_report": report_data,
            },
            overview_data={"ticker": clean_ticker, "company_name": company_name, "market": market},
            history_data={
                "candles": val_summary.candles_sample,
                "validation": quality_metrics.model_dump(),
            },
            summary=ai_narrative.executive_summary,
            limitations=ai_narrative.cleaning_transparency_notes,
        )
        db.add(report)
        db.commit()
        db.refresh(task)
        db.refresh(report)

        report_response = DatasetValidationReportResponse(
            report_id=report.report_id,
            task_id=task.task_id,
            ticker=clean_ticker,
            company_name=company_name,
            market=market,
            requested_period=payload.period,
            active_provider=active_provider,
            retrieval_timestamp=retrieved_at,
            latency_ms=latency_ms,
            validation_status=quality_metrics.validation_status,
            quality_metrics=quality_metrics,
            raw_snapshot=raw_snap,
            validated_summary=val_summary,
            provider_attempts=attempt_logs,
            issues=issues,
            ai_explanation=ai_narrative,
            download_url_json=f"/api/dataset/reports/{report.report_id}/download?format=json",
            download_url_csv=f"/api/dataset/reports/{report.report_id}/download?format=csv",
        )
        return report_response

    except Exception as exc:
        task.status = "Failed"
        task.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.error(f"Dataset collection task #{task.task_id} failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Automated dataset collection failed for {clean_ticker}: {str(exc)}",
        )


@router.get(
    "/reports",
    response_model=DatasetReportsHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="List authenticated user's dataset validation reports",
)
def list_dataset_validation_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DatasetReportsHistoryResponse:
    """
    Retrieves all dataset validation reports created by the current user with strict tenant isolation.
    """
    reports = (
        db.query(ResearchReport)
        .join(ResearchTask, ResearchReport.task_id == ResearchTask.task_id)
        .filter(ResearchTask.user_id == current_user.user_id)
        .order_by(ResearchReport.created_at.desc())
        .all()
    )

    items: List[DatasetReportListItem] = []
    for r in reports:
        rc = r.report_content or {}
        if rc.get("type") == "dataset_validation" and "validation_report" in rc:
            vr = rc["validation_report"]
            qm = vr.get("quality_metrics", {})
            vs = vr.get("validated_summary", {})
            items.append(
                DatasetReportListItem(
                    report_id=r.report_id,
                    task_id=r.task_id,
                    ticker=vr.get("ticker", r.task.ticker),
                    company_name=vr.get("company_name", r.task.company_name),
                    market=vr.get("market", r.task.market),
                    requested_period=vr.get("requested_period", r.task.requested_period),
                    data_source=vr.get("active_provider", "yfinance"),
                    validation_status=vr.get("validation_status", "WARNING"),
                    data_quality_score=qm.get("data_quality_score", 0.0),
                    valid_records=vs.get("valid_rows_count", vs.get("valid_records_count", 0)),
                    created_at=r.created_at.isoformat() if r.created_at else "",
                )
            )

    return DatasetReportsHistoryResponse(
        status="success",
        count=len(items),
        data=items,
    )


@router.get(
    "/reports/{report_id}",
    response_model=DatasetValidationReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get details of a specific dataset validation report",
)
def get_dataset_validation_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DatasetValidationReportResponse:
    """
    Fetches full report details with strict ownership verification.
    """
    report = (
        db.query(ResearchReport)
        .join(ResearchTask, ResearchReport.task_id == ResearchTask.task_id)
        .filter(ResearchReport.report_id == report_id)
        .first()
    )

    if not report or not report.task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset validation report #{report_id} was not found.",
        )

    # Multi-tenant user isolation enforcement
    if report.task.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: this validation report belongs to another user.",
        )

    rc = report.report_content or {}
    if rc.get("type") != "dataset_validation" or "validation_report" not in rc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report #{report_id} is not a dataset validation report.",
        )

    vr = rc["validation_report"]
    return DatasetValidationReportResponse(
        report_id=report.report_id,
        task_id=report.task_id,
        ticker=vr["ticker"],
        company_name=vr["company_name"],
        market=vr["market"],
        requested_period=vr["requested_period"],
        active_provider=vr["active_provider"],
        retrieval_timestamp=vr["retrieval_timestamp"],
        latency_ms=vr["latency_ms"],
        validation_status=vr["validation_status"],
        quality_metrics=vr["quality_metrics"],
        raw_snapshot=vr["raw_snapshot"],
        validated_summary=vr["validated_summary"],
        provider_attempts=vr.get("provider_attempts", []),
        issues=vr.get("issues", []),
        ai_explanation=vr["ai_explanation"],
        download_url_json=f"/api/dataset/reports/{report.report_id}/download?format=json",
        download_url_csv=f"/api/dataset/reports/{report.report_id}/download?format=csv",
    )


@router.get(
    "/reports/{report_id}/download",
    summary="Download dataset validation report or clean dataset as JSON or CSV",
)
def download_dataset_report(
    report_id: int,
    format: str = Query("json", pattern="^(json|csv)$", description="Export format: json or csv"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Exports report audit trail as JSON or validated OHLCV candles as CSV.
    Strictly validates user ownership.
    """
    report = (
        db.query(ResearchReport)
        .join(ResearchTask, ResearchReport.task_id == ResearchTask.task_id)
        .filter(ResearchReport.report_id == report_id)
        .first()
    )

    if not report or not report.task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if report.task.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")

    rc = report.report_content or {}
    vr = rc.get("validation_report", {})
    ticker = vr.get("ticker", "dataset").lower()

    if format == "csv":
        val_summary = vr.get("validated_summary", {})
        candles = val_summary.get("candles_sample", [])
        if not candles:
            # Fallback to history data candles
            candles = report.history_data.get("candles", [])

        if not candles:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No validated candle records to export.")

        df = pd.DataFrame(candles)
        # Drop internal references if present
        if "_raw_row_id" in df.columns:
            df = df.drop(columns=["_raw_row_id"])
        if "source_row_id" in df.columns:
            df = df.drop(columns=["source_row_id"])

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{ticker}_validated_ohlcv.csv"'},
        )

    # JSON export (Complete Audit Trail)
    json_content = json.dumps(vr, indent=2, default=str)
    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{ticker}_validation_report.json"'},
    )
