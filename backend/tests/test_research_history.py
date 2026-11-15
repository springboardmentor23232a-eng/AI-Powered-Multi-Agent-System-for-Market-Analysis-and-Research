"""API tests for research history.

Module 7 will create research tasks through the agent workflow. Here we insert
tasks directly into the database to test ownership, ordering and pagination.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models import ResearchTask, User
from tests.conftest import API, auth_headers_for

URL = f"{API}/research/history"


def create_tasks(db_session, email, tickers):
    user = db_session.scalar(select(User).where(User.email == email))
    start = datetime(2026, 1, 1, tzinfo=UTC)
    for index, ticker in enumerate(tickers):
        db_session.add(
            ResearchTask(
                user_id=user.user_id,
                ticker=ticker,
                market="NSE",
                requested_period="1Y",
                created_at=start + timedelta(hours=index),
            )
        )
    db_session.commit()


def test_history_is_empty_for_new_user(client, auth_headers):
    response = client.get(URL, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


def test_history_lists_own_tasks_newest_first(client, auth_headers, db_session):
    create_tasks(db_session, "alice@example.com", ["INFY", "TCS", "WIPRO"])
    body = client.get(URL, headers=auth_headers).json()
    assert body["total"] == 3
    assert [t["ticker"] for t in body["items"]] == ["WIPRO", "TCS", "INFY"]
    assert body["items"][0]["status"] == "pending"
    assert body["items"][0]["completed_at"] is None


def test_history_pagination(client, auth_headers, db_session):
    create_tasks(db_session, "alice@example.com", [f"T{i}" for i in range(5)])
    body = client.get(URL, headers=auth_headers, params={"limit": 2, "offset": 2}).json()
    assert body["total"] == 5
    assert [t["ticker"] for t in body["items"]] == ["T2", "T1"]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_history_rejects_invalid_pagination(client, auth_headers, params):
    assert client.get(URL, headers=auth_headers, params=params).status_code == 422


def test_history_is_private_to_each_user(client, auth_headers, db_session):
    auth_headers_for(client, email="bob@example.com")
    create_tasks(db_session, "bob@example.com", ["AAPL"])
    assert client.get(URL, headers=auth_headers).json()["total"] == 0


def test_deleting_user_deletes_their_tasks(client, auth_headers, db_session):
    create_tasks(db_session, "alice@example.com", ["INFY"])
    user = db_session.scalar(select(User).where(User.email == "alice@example.com"))
    db_session.delete(user)
    db_session.commit()
    assert db_session.scalars(select(ResearchTask)).all() == []
