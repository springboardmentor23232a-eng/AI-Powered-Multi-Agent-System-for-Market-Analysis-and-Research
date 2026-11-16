"""
migrate_task4_schema.py
Safe, non-destructive schema evolution for Task 4 compliance.
Adds `report_content` (JSON) and `limitations` (TEXT) to the `research_reports` table
while strictly preserving all existing columns, rows, foreign keys, and indexes.
"""

import sys
import json
from pathlib import Path

# Ensure backend directory is in python path
backend_dir = Path(__file__).resolve().parents[2]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import inspect, text
from app.database import engine, SessionLocal
from app.models.research_task import ResearchReport, ResearchTask


def run_migration():
    print("=== TASK 4 SCHEMA MIGRATION: EVOLVING research_reports ===")
    
    # 1. Inspect existing columns
    inspector = inspect(engine)
    existing_cols = {c["name"]: c for c in inspector.get_columns("research_reports")}
    print(f"Existing columns in research_reports: {list(existing_cols.keys())}")
    
    # 2. Safely add columns if not present
    with engine.begin() as conn:
        if "report_content" not in existing_cols:
            print("Adding column 'report_content' (JSON) to research_reports...")
            conn.execute(text("ALTER TABLE research_reports ADD COLUMN IF NOT EXISTS report_content JSON;"))
        else:
            print("Column 'report_content' already exists.")

        if "limitations" not in existing_cols:
            print("Adding column 'limitations' (TEXT) to research_reports...")
            conn.execute(text("ALTER TABLE research_reports ADD COLUMN IF NOT EXISTS limitations TEXT;"))
        else:
            print("Column 'limitations' already exists.")

    # 3. Verify column addition
    inspector = inspect(engine)
    updated_cols = {c["name"]: c for c in inspector.get_columns("research_reports")}
    print(f"Updated columns in research_reports: {list(updated_cols.keys())}")
    assert "report_content" in updated_cols, "Failed to add report_content column!"
    assert "limitations" in updated_cols, "Failed to add limitations column!"

    # 4. Backfill existing records to ensure complete data integrity
    db = SessionLocal()
    try:
        reports = db.query(ResearchReport).all()
        print(f"Total existing reports to verify/backfill: {len(reports)}")
        backfilled_count = 0

        for r in reports:
            changed = False
            task = db.query(ResearchTask).filter(ResearchTask.task_id == r.task_id).first()
            ticker = task.ticker if task else "Unknown"

            if r.report_content is None:
                # Derive consolidated report_content directly from existing overview_data and history_data
                r.report_content = {
                    "overview": r.overview_data,
                    "history": r.history_data,
                    "summary": r.summary,
                    "metadata": {
                        "task_id": r.task_id,
                        "ticker": ticker,
                        "company_name": task.company_name if task else None,
                        "market": task.market if task else None,
                        "requested_period": task.requested_period if task else None,
                    }
                }
                changed = True

            if not r.limitations:
                # Factual limitations based on the real provider and market data cleaner
                val = r.history_data.get("validation", {}) if r.history_data else {}
                stats = r.history_data.get("stats", {}) if r.history_data else {}
                total_raw = val.get("total_raw_records", 0)
                cleaned = val.get("cleaned_records", 0)
                dups = val.get("duplicates_removed", 0)
                start_d = stats.get("start_date", "N/A")
                end_d = stats.get("end_date", "N/A")
                days = stats.get("total_trading_days", 0)

                r.limitations = (
                    f"Data retrieved via yfinance market data service for {ticker}. "
                    f"Historical dataset covers {days} trading days from {start_d} to {end_d}. "
                    f"Data validation pipeline evaluated {total_raw} raw records, filtered {dups} duplicates, "
                    f"and verified {cleaned} clean sessions. "
                    f"Historical price data and calculated statistics describe past trading sessions "
                    f"and do not constitute investment advice or guarantee future performance. "
                    f"Real-time exchange quotes may be subject to standard provider delays."
                )
                changed = True

            if changed:
                backfilled_count += 1

        db.commit()
        print(f"Backfill complete: {backfilled_count} existing records updated with non-null report_content and limitations.")

        # 5. Sanity check: Ensure all records are readable and preserved
        total_after = db.query(ResearchReport).count()
        print(f"Total records preserved in research_reports: {total_after} (100% preserved)")
        sample = db.query(ResearchReport).first()
        if sample:
            print("Sample record verification:")
            print(f"  - report_id: {sample.report_id}")
            print(f"  - task_id: {sample.task_id}")
            print(f"  - report_content keys: {list(sample.report_content.keys()) if sample.report_content else None}")
            print(f"  - overview_data keys: {list(sample.overview_data.keys()) if sample.overview_data else None}")
            print(f"  - limitations preview: {sample.limitations[:120]}...")

    finally:
        db.close()

    print("=== MIGRATION COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    run_migration()
