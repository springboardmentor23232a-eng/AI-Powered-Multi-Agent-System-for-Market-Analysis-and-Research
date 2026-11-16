import pytest
from app.models.research_task import ResearchTask, ResearchReport
from app.config import settings


def register_and_login(client, email: str, name: str = "Test User"):
    # Register
    reg_payload = {
        "fullName": name,
        "email": email,
        "password": "Password123!",
        "confirmPassword": "Password123!",
    }
    client.post("/api/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": email,
        "password": "Password123!",
    }
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200
    return res.json()["data"]


def test_research_task_creation_and_persistence(client, db_session):
    user = register_and_login(client, "user_task_test@example.com", "Task Tester")

    # 1. Create research task
    task_payload = {
        "ticker": "INFY.NS",
        "period": "1mo",
    }
    res = client.post("/api/research/tasks", json=task_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "success"
    task = data["task"]
    assert task["ticker"] == "INFY.NS"
    assert task["status"] == "Completed"
    assert task["user_id"] == user["user_id"]
    assert task["has_report"] is True
    assert data["report"] is not None
    assert "overview_data" in data["report"]
    assert "history_data" in data["report"]
    assert "report_content" in data["report"]
    assert data["report"]["report_content"] is not None
    assert "metadata" in data["report"]["report_content"]
    assert "limitations" in data["report"]
    assert data["report"]["limitations"] is not None
    assert "yfinance" in data["report"]["limitations"]

    # 2. Verify persistence in PostgreSQL
    db_task = db_session.query(ResearchTask).filter(ResearchTask.task_id == task["task_id"]).first()
    assert db_task is not None
    assert db_task.ticker == "INFY.NS"
    assert db_task.status == "Completed"
    assert db_task.user_id == user["user_id"]

    # 3. Verify report linked in PostgreSQL with new schema compliance fields
    db_report = db_session.query(ResearchReport).filter(ResearchReport.task_id == task["task_id"]).first()
    assert db_report is not None
    assert db_report.overview_data["ticker"] == "INFY.NS"
    assert db_report.report_content is not None
    assert db_report.limitations is not None
    assert len(db_report.limitations) > 20


def test_user_specific_history_isolation(client):
    # Register and create task as User A
    user_a = register_and_login(client, "user_a@example.com", "User Alpha")
    task_a_res = client.post("/api/research/tasks", json={"ticker": "INFY.NS", "period": "1mo"})
    assert task_a_res.status_code == 201
    task_a_id = task_a_res.json()["task"]["task_id"]

    # Verify User A's history contains task A
    hist_a = client.get("/api/research/history")
    assert hist_a.status_code == 200
    task_ids_a = [t["task_id"] for t in hist_a.json()["data"]]
    assert task_a_id in task_ids_a

    # Now login as User B
    client.cookies.clear()
    user_b = register_and_login(client, "user_b@example.com", "User Beta")
    task_b_res = client.post("/api/research/tasks", json={"ticker": "TCS.NS", "period": "3mo"})
    assert task_b_res.status_code == 201
    task_b_id = task_b_res.json()["task"]["task_id"]

    # Verify User B's history contains task B, and NOT task A
    hist_b = client.get("/api/research/history")
    assert hist_b.status_code == 200
    task_ids_b = [t["task_id"] for t in hist_b.json()["data"]]
    assert task_b_id in task_ids_b
    assert task_a_id not in task_ids_b  # Strict user isolation!

    # Verify User B CANNOT open User A's report (must return 404)
    cross_access_res = client.get(f"/api/research/tasks/{task_a_id}")
    assert cross_access_res.status_code == 404
    assert "not found" in cross_access_res.json()["detail"].lower()

    # User B CAN open their own report (must return 200)
    own_access_res = client.get(f"/api/research/tasks/{task_b_id}")
    assert own_access_res.status_code == 200
    assert own_access_res.json()["task"]["task_id"] == task_b_id


def test_unauthenticated_research_requests_rejected(client):
    client.cookies.clear()

    # POST /api/research/tasks
    res_post = client.post("/api/research/tasks", json={"ticker": "AAPL", "period": "1mo"})
    assert res_post.status_code == 401
    assert "Authentication required" in res_post.json()["detail"]

    # GET /api/research/history
    res_get = client.get("/api/research/history")
    assert res_get.status_code == 401

    # GET /api/research/tasks/1
    res_detail = client.get("/api/research/tasks/1")
    assert res_detail.status_code == 401


def test_failed_research_task_recorded(client, db_session):
    register_and_login(client, "fail_tester@example.com", "Fail Tester")

    # Send an invalid ticker symbol that fails market lookup
    bad_payload = {"ticker": "NOTREALXYZ", "period": "1mo"}
    res = client.post("/api/research/tasks", json=bad_payload)
    assert res.status_code == 400
    assert "failed" in res.json()["detail"].lower()

    # Verify the failed task was committed in PostgreSQL with status 'Failed'
    failed_task = (
        db_session.query(ResearchTask)
        .filter(ResearchTask.ticker == "NOTREALXYZ")
        .first()
    )
    assert failed_task is not None
    assert failed_task.status == "Failed"
    assert failed_task.completed_at is not None
