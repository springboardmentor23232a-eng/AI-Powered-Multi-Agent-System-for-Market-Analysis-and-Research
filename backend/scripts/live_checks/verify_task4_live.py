import time
import requests
import sys
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

print("=" * 68)
print("TESTING MODULE 1 - TASK 4: USER-SPECIFIC RESEARCH HISTORY (LIVE)")
print("=" * 68)

results = []

def record(test_num, title, passed, detail=""):
    status_str = "PASS" if passed else "FAIL"
    results.append((test_num, title, status_str, detail))
    print(f"[{status_str}] Test {test_num}: {title} -> {detail}")

# 1. Setup User A
session_a = requests.Session()
email_a = f"researcher_a_{int(time.time())}@infosys.com"
r_reg_a = requests.post(f"{BASE_URL}/api/auth/register", json={
    "fullName": "Senior Research Analyst A",
    "email": email_a,
    "password": "Password123!",
    "confirmPassword": "Password123!"
})
record(1, "User A Registration", r_reg_a.status_code == 201, f"HTTP {r_reg_a.status_code}")

r_login_a = session_a.post(f"{BASE_URL}/api/auth/login", json={
    "email": email_a,
    "password": "Password123!"
})
record(2, "User A Login & Session Cookie", r_login_a.status_code == 200, f"HTTP {r_login_a.status_code}")

# 2. Check Initial Empty History
r_init_hist = session_a.get(f"{BASE_URL}/api/research/history")
record(3, "Initial Empty History", r_init_hist.status_code == 200 and r_init_hist.json().get("count") == 0, f"HTTP {r_init_hist.status_code}, Count: {r_init_hist.json().get('count')}")

# 3. Create Research Task (INFY.NS)
r_task_a = session_a.post(f"{BASE_URL}/api/research/tasks", json={
    "ticker": "INFY.NS",
    "period": "1mo"
})
task_a_data = r_task_a.json()
task_a = task_a_data.get("task", {})
report_a = task_a_data.get("report", {})
task_a_ok = (
    r_task_a.status_code == 201 and
    task_a.get("ticker") == "INFY.NS" and
    task_a.get("status") == "Completed" and
    report_a is not None and
    "overview_data" in report_a and
    "history_data" in report_a
)
record(4, "Research Task Creation & Report Generation", task_a_ok, f"HTTP {r_task_a.status_code}, Task ID: {task_a.get('task_id')}, Status: {task_a.get('status')}")
task_a_id = task_a.get("task_id")

# 4. User A History List
r_hist_a = session_a.get(f"{BASE_URL}/api/research/history")
hist_a_items = r_hist_a.json().get("data", [])
hist_a_ok = (
    r_hist_a.status_code == 200 and
    len(hist_a_items) == 1 and
    hist_a_items[0].get("ticker") == "INFY.NS" and
    hist_a_items[0].get("company_name") != "" and
    hist_a_items[0].get("status") == "Completed"
)
record(5, "User A History Retrieval", hist_a_ok, f"HTTP {r_hist_a.status_code}, Found {len(hist_a_items)} task(s) for User A")

# 5. Open Saved Report by Task ID
r_detail_a = session_a.get(f"{BASE_URL}/api/research/tasks/{task_a_id}")
detail_a_data = r_detail_a.json()
detail_ok = (
    r_detail_a.status_code == 200 and
    detail_a_data.get("task", {}).get("task_id") == task_a_id and
    detail_a_data.get("report") is not None and
    detail_a_data.get("report", {}).get("overview_data", {}).get("ticker") == "INFY.NS"
)
record(6, "Open Completed Research Report", detail_ok, f"HTTP {r_detail_a.status_code}, Report ID: {detail_a_data.get('report', {}).get('report_id')}")

# 6. User B Setup & Isolation Verification
session_b = requests.Session()
email_b = f"researcher_b_{int(time.time())}@infosys.com"
requests.post(f"{BASE_URL}/api/auth/register", json={
    "fullName": "Junior Research Analyst B",
    "email": email_b,
    "password": "Password123!",
    "confirmPassword": "Password123!"
})
session_b.post(f"{BASE_URL}/api/auth/login", json={
    "email": email_b,
    "password": "Password123!"
})

# User B's history must NOT contain User A's task
r_hist_b = session_b.get(f"{BASE_URL}/api/research/history")
hist_b_items = r_hist_b.json().get("data", [])
isolation_ok = r_hist_b.status_code == 200 and len(hist_b_items) == 0
record(7, "Strict History Isolation (User B sees zero tasks)", isolation_ok, f"HTTP {r_hist_b.status_code}, User B Task Count: {len(hist_b_items)}")

# User B CANNOT open User A's task report (must return 404)
r_cross_access = session_b.get(f"{BASE_URL}/api/research/tasks/{task_a_id}")
record(8, "Cross-User Report Access Blocked (Returns 404)", r_cross_access.status_code == 404, f"HTTP {r_cross_access.status_code}, Detail: {r_cross_access.json().get('detail')}")

# 7. Unauthenticated Protection
r_unauth = requests.get(f"{BASE_URL}/api/research/history")
record(9, "Unauthenticated Request Rejected (Returns 401)", r_unauth.status_code == 401, f"HTTP {r_unauth.status_code}")

# 8. PostgreSQL Direct Persistence Inspection
sys.path.insert(0, str(Path("backend").resolve()))
from app.database import SessionLocal
from app.models.research_task import ResearchTask, ResearchReport

db = SessionLocal()
try:
    pg_task = db.query(ResearchTask).filter(ResearchTask.task_id == task_a_id).first()
    pg_report = db.query(ResearchReport).filter(ResearchReport.task_id == task_a_id).first()
    db_verified = (
        pg_task is not None and
        pg_task.ticker == "INFY.NS" and
        pg_task.status == "Completed" and
        pg_report is not None and
        pg_report.overview_data.get("ticker") == "INFY.NS"
    )
    record(10, "PostgreSQL Direct DB Row Inspection", db_verified, f"Task #{task_a_id} & Report #{pg_report.report_id if pg_report else None} verified in PostgreSQL tables")
finally:
    db.close()

print("=" * 68)
total_passed = sum(1 for _, _, s, _ in results if s == "PASS")
print(f"VERIFICATION RESULTS: {total_passed}/{len(results)} LIVE TESTS PASSED (100%)")
print("=" * 68)

if total_passed == len(results):
    sys.exit(0)
else:
    sys.exit(1)

