"""
verify_compliance_live.py
Live end-to-end verification script for Task 4 Final Schema Compliance.
Tests live against running FastAPI backend and PostgreSQL database.
"""

import sys
import time
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def run_live_verification():
    print("=== LIVE VERIFICATION: TASK 4 SCHEMA COMPLIANCE ===")
    
    # 1. Health check
    res = requests.get(f"{BASE_URL}/api/health", timeout=5)
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] 1. Backend health check: 200 OK")

    # 2. Register & Login User A
    session_a = requests.Session()
    email_a = f"compliance_user_a_{int(time.time())}@example.com"
    reg_payload = {
        "fullName": "Compliance Tester Alpha",
        "email": email_a,
        "password": "Password123!",
        "confirmPassword": "Password123!",
    }
    res_reg = session_a.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
    assert res_reg.status_code == 201, f"Registration failed: {res_reg.text}"
    
    res_login = session_a.post(f"{BASE_URL}/api/auth/login", json={"email": email_a, "password": "Password123!"})
    assert res_login.status_code == 200, f"Login failed: {res_login.text}"
    user_a = res_login.json()["data"]
    print(f"[PASS] 2. User A registered and logged in: {user_a['email']}")

    # 3. Create a new research task on live backend
    task_res = session_a.post(f"{BASE_URL}/api/research/tasks", json={"ticker": "INFY.NS", "period": "1mo"})
    assert task_res.status_code == 201, f"Task creation failed: {task_res.text}"
    task_data = task_res.json()
    task = task_data["task"]
    report = task_data["report"]
    task_id = task["task_id"]

    assert task["status"] == "Completed"
    assert report is not None
    assert "report_content" in report
    assert report["report_content"] is not None
    assert "metadata" in report["report_content"]
    assert "limitations" in report
    assert report["limitations"] is not None
    assert "overview_data" in report
    assert "history_data" in report
    assert "summary" in report
    print(f"[PASS] 3. Research task #{task_id} executed and returned report_content & limitations")
    print(f"       Limitations snippet: {report['limitations'][:90]}...")

    # 4. Fetch specific task detail and report via GET /api/research/tasks/{task_id}
    detail_res = session_a.get(f"{BASE_URL}/api/research/tasks/{task_id}")
    assert detail_res.status_code == 200
    retrieved_report = detail_res.json()["report"]
    assert retrieved_report["report_id"] == report["report_id"]
    assert retrieved_report["limitations"] == report["limitations"]
    print(f"[PASS] 4. GET /api/research/tasks/{task_id} retrieved verified report with limitations")

    # 5. Fetch research history via GET /api/research/history
    hist_res = session_a.get(f"{BASE_URL}/api/research/history")
    assert hist_res.status_code == 200
    history_tasks = hist_res.json()["data"]
    assert any(t["task_id"] == task_id for t in history_tasks)
    print(f"[PASS] 5. GET /api/research/history returned {len(history_tasks)} user tasks")

    # 6. Verify cross-user isolation: User B cannot access User A's report
    session_b = requests.Session()
    email_b = f"compliance_user_b_{int(time.time())}@example.com"
    session_b.post(f"{BASE_URL}/api/auth/register", json={
        "fullName": "Compliance Tester Beta",
        "email": email_b,
        "password": "Password123!",
        "confirmPassword": "Password123!",
    })
    session_b.post(f"{BASE_URL}/api/auth/login", json={"email": email_b, "password": "Password123!"})

    cross_res = session_b.get(f"{BASE_URL}/api/research/tasks/{task_id}")
    assert cross_res.status_code == 404, f"Cross-user access was not blocked! Code: {cross_res.status_code}"
    print(f"[PASS] 6. Cross-user protection verified: User B received 404 attempting to open User A's task #{task_id}")

    # 7. Unauthenticated access rejected
    unauth_res = requests.get(f"{BASE_URL}/api/research/tasks/{task_id}")
    assert unauth_res.status_code == 401
    print("[PASS] 7. Unauthenticated access rejected: 401 Unauthorized")

    # 8. Check direct PostgreSQL database state
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.database import SessionLocal
    from app.models.research_task import ResearchReport

    db = SessionLocal()
    try:
        all_reports = db.query(ResearchReport).all()
        print(f"[PASS] 8. Direct DB inspection: {len(all_reports)} total reports in PostgreSQL")
        for r in all_reports:
            assert r.report_content is not None, f"Report #{r.report_id} has null report_content"
            assert r.limitations is not None, f"Report #{r.report_id} has null limitations"
            assert r.overview_data is not None, f"Report #{r.report_id} has null overview_data"
            assert r.history_data is not None, f"Report #{r.report_id} has null history_data"
        print("[PASS] 9. 100% of persisted reports satisfy non-null compliance for report_content & limitations")
    finally:
        db.close()

    print("\nALL 9 LIVE VERIFICATION CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_live_verification()

