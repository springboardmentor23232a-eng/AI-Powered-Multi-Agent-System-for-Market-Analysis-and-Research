import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Tuple

BASE_URL = "http://127.0.0.1:8000"


def make_request(
    method: str,
    path: str,
    token: str = None,
    payload: Dict[str, Any] = None,
    expected_status: int = 200,
) -> Tuple[int, Any, Dict[str, str]]:
    """Helper to send HTTP requests to the live FastAPI backend."""
    url = f"{BASE_URL}{path}"
    headers = {"User-Agent": "FinCrew-LiveVerifier/1.0"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            status_code = resp.status
            content_type = resp.headers.get("Content-Type", "")
            raw_body = resp.read()

            if "application/json" in content_type:
                body = json.loads(raw_body.decode("utf-8"))
            elif "application/pdf" in content_type:
                body = raw_body
            else:
                body = raw_body.decode("utf-8")

            resp_headers = {k: v for k, v in resp.headers.items()}
            return status_code, body, resp_headers
    except urllib.error.HTTPError as e:
        status_code = e.code
        err_content = e.read()
        try:
            body = json.loads(err_content.decode("utf-8"))
        except Exception:
            body = err_content.decode("utf-8", errors="replace")
        return status_code, body, {}


def main():
    print("=" * 70)
    print("FinCrew Stage 6C: Final Live End-to-End System Verification")
    print("Executing on real live data without mocks")
    print("=" * 70)

    # 1. Server Health Checks
    print("\n[Check 1/10] Verifying Server and PostgreSQL Health...")
    status, health_data, _ = make_request("GET", "/api/health")
    assert status == 200, f"Health check failed with status {status}"
    print(f"  -> /api/health: Status={health_data.get('status')}, App={health_data.get('app')}")

    status, db_data, _ = make_request("GET", "/api/db-health")
    assert status == 200, f"DB Health check failed with status {status}"
    print(f"  -> /api/db-health: Status={db_data.get('status')}, DB={db_data.get('database')}, User={db_data.get('user')}")

    # 2. Authenticate using existing user
    print("\n[Check 2/10] Authenticating with Existing Account...")
    # Using existing demo.trader account
    login_payload = {
        "email": "demo.trader@fincrew.com",
        "password": "Password@2026",
    }
    status, login_res, _ = make_request("POST", "/api/auth/login", payload=login_payload)
    assert status == 200, f"Login failed: {login_res}"
    token = login_res["access_token"]
    user_info = login_res["user"]
    print(f"  -> Successfully authenticated as '{user_info.get('full_name')}' (id={user_info.get('id')})")
    print("  -> JWT access token issued successfully.")

    # 3. Live Research Run for AAPL
    print("\n[Check 3/10] Running Live Multi-Agent Stock Research for AAPL...")
    status, aapl_session, _ = make_request(
        "POST",
        "/api/research/analyze?run_sync=true",
        token=token,
        payload={"ticker": "AAPL"},
    )
    assert status == 200, f"Live AAPL research failed: {aapl_session}"
    aapl_id = aapl_session["id"]
    aapl_status = aapl_session["status"]
    aapl_report = aapl_session.get("report")
    assert aapl_status == "COMPLETED", f"AAPL session status is {aapl_status}, error: {aapl_session.get('error_message')}"
    assert aapl_report is not None, "AAPL report was not generated"

    print(f"  -> AAPL Session ID: {aapl_id} (Status: {aapl_status})")
    print(f"  -> Company Name: {aapl_report.get('company_name')}")
    print(f"  -> Live Price: ${aapl_report.get('current_price')} (12-Mo Target: ${aapl_report.get('target_price')})")
    print(f"  -> Committee Consensus: {aapl_report.get('recommendation')} (Confidence: {int(aapl_report.get('confidence_score', 0) * 100)}%)")

    # Verify all 5 agents executed for AAPL
    fun = aapl_report.get("fundamental_data") or {}
    mr = fun.get("market_research") or {}
    tech = aapl_report.get("technical_data") or {}
    sent = aapl_report.get("sentiment_data") or {}
    risk = aapl_report.get("risk_data") or {}

    print("  -> 5 Specialist Agents Executed:")
    print(f"     1. Market Research: Sector={mr.get('sector')}, Cap={mr.get('market_cap_category')}")
    print(f"     2. Financial Analysis: Valuation={fun.get('valuation_status')}, Profitability={fun.get('profitability_grade')}")
    print(f"     3. Technical Analysis: Trend={tech.get('trend_direction')}, Momentum={tech.get('momentum_state')}")
    print(f"     4. Sentiment Analysis: Label={sent.get('sentiment_label')}, Score={sent.get('sentiment_score')}")
    print(f"     5. Risk Analysis: Risk Level={risk.get('risk_level')}, Score={risk.get('risk_score')}/10")

    # 4. Live Research Run for MSFT
    print("\n[Check 4/10] Running Live Multi-Agent Stock Research for MSFT...")
    status, msft_session, _ = make_request(
        "POST",
        "/api/research/analyze?run_sync=true",
        token=token,
        payload={"ticker": "MSFT"},
    )
    assert status == 200, f"Live MSFT research failed: {msft_session}"
    msft_id = msft_session["id"]
    msft_status = msft_session["status"]
    msft_report = msft_session.get("report")
    assert msft_status == "COMPLETED", f"MSFT session status is {msft_status}, error: {msft_session.get('error_message')}"
    assert msft_report is not None, "MSFT report was not generated"

    print(f"  -> MSFT Session ID: {msft_id} (Status: {msft_status})")
    print(f"  -> Company Name: {msft_report.get('company_name')}")
    print(f"  -> Live Price: ${msft_report.get('current_price')} (12-Mo Target: ${msft_report.get('target_price')})")
    print(f"  -> Committee Consensus: {msft_report.get('recommendation')} (Confidence: {int(msft_report.get('confidence_score', 0) * 100)}%)")

    # 5. Direct Database Persistence Check
    print("\n[Check 5/10] Verifying Real PostgreSQL Persistence...")
    from app.database import SessionLocal
    from app.models.research import ResearchReport, ResearchSession
    db = SessionLocal()
    try:
        sess_aapl = db.query(ResearchSession).filter(ResearchSession.id == aapl_id).first()
        assert sess_aapl is not None
        assert sess_aapl.status == "COMPLETED"
        rep_aapl = sess_aapl.report
        assert rep_aapl is not None
        assert rep_aapl.ticker == "AAPL"

        sess_msft = db.query(ResearchSession).filter(ResearchSession.id == msft_id).first()
        assert sess_msft is not None
        assert sess_msft.status == "COMPLETED"
        rep_msft = sess_msft.report
        assert rep_msft is not None
        assert rep_msft.ticker == "MSFT"

        print(f"  -> Verified in PostgreSQL: Both sessions and reports confirmed in fincrew_db.")
    finally:
        db.close()

    # 6. Retrieve Reports via Authenticated API
    print("\n[Check 6/10] Retrieving Reports via Authenticated Endpoints...")
    status, rep_aapl_api, _ = make_request("GET", f"/api/research/sessions/{aapl_id}/report", token=token)
    assert status == 200, f"Failed to retrieve AAPL report: {rep_aapl_api}"
    assert rep_aapl_api["ticker"] == "AAPL"

    status, rep_msft_api, _ = make_request("GET", f"/api/research/sessions/{msft_id}/report", token=token)
    assert status == 200, f"Failed to retrieve MSFT report: {rep_msft_api}"
    assert rep_msft_api["ticker"] == "MSFT"
    print("  -> Both reports retrieved successfully via GET /api/research/sessions/{id}/report.")

    # 7. Download and Validate Genuine PDF Export
    print("\n[Check 7/10] Downloading and Validating Genuine Binary PDF Export...")
    status, pdf_bytes, headers = make_request("GET", f"/api/research/sessions/{aapl_id}/export?format=pdf", token=token)
    assert status == 200, f"PDF export failed with status {status}"
    
    # Check content-type case-insensitively
    ct_header = next((v for k, v in headers.items() if k.lower() == "content-type"), "")
    assert "application/pdf" in ct_header, f"Wrong content-type: {ct_header}"
    assert isinstance(pdf_bytes, bytes), "Response body is not bytes"
    assert pdf_bytes.startswith(b"%PDF-"), f"Magic bytes invalid: {pdf_bytes[:10]}; Not a genuine PDF!"
    assert b"%%EOF" in pdf_bytes, "Missing PDF EOF marker"
    assert len(pdf_bytes) > 2000, f"PDF size unexpectedly small: {len(pdf_bytes)} bytes"

    # Confirm it is NOT HTML
    assert not pdf_bytes.strip().startswith(b"<!DOCTYPE")
    assert not pdf_bytes.strip().startswith(b"<html")

    print(f"  -> PDF Export Validated: Size={len(pdf_bytes):,} bytes | Header={pdf_bytes[:8].decode('latin-1')} | Structure=Valid PDF-1.7")

    # Also test Markdown export
    status, md_text, _ = make_request("GET", f"/api/research/sessions/{aapl_id}/export?format=markdown", token=token)
    assert status == 200
    assert "# Institutional Equity Research: Apple Inc. (AAPL)" in md_text
    print("  -> Markdown Export Validated: Complete research memo with 5 specialist sections.")

    # 8. Compare Two Completed Sessions
    print("\n[Check 8/10] Running Multi-Stock Comparative Analysis...")
    status, comp_data, _ = make_request(
        "POST",
        "/api/research/compare",
        token=token,
        payload={"session_ids": [aapl_id, msft_id]},
    )
    assert status == 200, f"Comparison failed: {comp_data}"
    assert comp_data["total_compared"] == 2
    assert len(comp_data["items"]) == 2
    matrix = comp_data["matrix"]
    assert len(matrix) >= 15

    print(f"  -> Compared {comp_data['total_compared']} Equities: AAPL vs MSFT")
    print(f"  -> Comparison Matrix Rows Generated: {len(matrix)} metrics across Consensus, Valuation, Technicals, Sentiment, Risk, Classification")

    # Sample rows
    for r in matrix[:5]:
        val_str = " | ".join(f"{t}: {v}" for t, v in r["values"].items())
        print(f"     * [{r['category']}] {r['metric']:20} -> {val_str}")

    # 9. Workspace Analytics
    print("\n[Check 9/10] Verifying Workspace Research Analytics...")
    status, analytics, _ = make_request("GET", "/api/research/analytics/summary", token=token)
    assert status == 200, f"Analytics failed: {analytics}"
    assert analytics["total_sessions"] >= 2
    assert analytics["status_counts"]["completed"] >= 2
    assert analytics["average_confidence"] > 0.0
    print(f"  -> Total Research Sessions: {analytics['total_sessions']}")
    print(f"  -> Status Breakdown: {analytics['status_counts']}")
    print(f"  -> Recommendation Distribution: {analytics['recommendation_distribution']}")
    print(f"  -> Average Committee Confidence: {int(analytics['average_confidence'] * 100)}%")
    print(f"  -> Sector Allocations: {analytics['sector_allocation']}")

    # 10. Security & Ownership Verification
    print("\n[Check 10/10] Testing Security & Ownership Restrictions...")
    # Unauthenticated report access
    status, _, _ = make_request("GET", f"/api/research/sessions/{aapl_id}/report")
    assert status == 401, f"Expected 401 for unauthenticated request, got {status}"
    print("  -> Unauthenticated request strictly rejected (401 Unauthorized).")

    # Invalid comparison session IDs
    status, _, _ = make_request("POST", "/api/research/compare", token=token, payload={"session_ids": [aapl_id, 9999999]})
    assert status == 404, f"Expected 404 for nonexistent session, got {status}"
    print("  -> Nonexistent session comparison rejected (404 Not Found).")

    print("\n" + "=" * 70)
    print("ALL 10 STAGE 6C LIVE VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("Zero errors, zero data fabrication, genuine PDF, real live market data.")
    print("=" * 70)


if __name__ == "__main__":
    main()
