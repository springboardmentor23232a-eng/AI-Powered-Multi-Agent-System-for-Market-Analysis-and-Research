import pytest

from app.api.research import get_llm, get_news_provider
from app.api.stocks import get_provider
from app.main import app
from app.services.llm import TemplateLLM
from tests.fakes import FIN, FakeNews, FakeProvider, article, make_ohlcv


@pytest.fixture()
def api(file_client):
    app.dependency_overrides[get_provider] = lambda: FakeProvider(df=make_ohlcv(400), financials=FIN)
    app.dependency_overrides[get_news_provider] = lambda: FakeNews([article("TCS wins large deal", 1)])
    app.dependency_overrides[get_llm] = lambda: TemplateLLM()
    yield file_client


def login(c, email="a@b.com"):
    t = c.post("/auth/register", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {t}"}


def test_full_research_flow(api):
    h = login(api)
    r = api.post("/research", json={"ticker": "tcs"}, headers=h)
    assert r.status_code == 202
    tid = r.json()["task_id"]

    d = api.get(f"/research/{tid}", headers=h).json()           # background task has finished
    assert d["status"] == "completed" and d["ticker"] == "TCS" and d["period"] == "2y"
    assert {a["agent"] for a in d["agents"]} == {"fundamental", "technical", "news", "risk"}
    assert d["evidence"]["percent"] == 100.0 and d["latency_ms"] is not None

    rep = api.get(f"/research/{tid}/report", headers=h).json()
    assert "Evidence score" in rep["content"] and rep["summary"]
    md = api.get(f"/research/{tid}/report?format=md", headers=h)
    assert md.headers["content-type"].startswith("text/markdown") and "attachment" in md.headers["content-disposition"]

    claims = api.get(f"/research/{tid}/claims", headers=h).json()
    assert {c["type"] for c in claims} == {"FACT", "CALCULATED", "INTERPRETATION"} and all(c["verified"] for c in claims)
    assert api.get(f"/research/{tid}/contradictions", headers=h).status_code == 200
    tech = api.get(f"/research/{tid}/agents/technical", headers=h).json()
    assert tech["status"] == "success" and "chart" in tech["data"]

    hist = api.get("/research", headers=h).json()
    assert [t["task_id"] for t in hist] == [tid]


def test_validation_and_isolation(api):
    h1, h2 = login(api, "a@b.com"), login(api, "c@d.com")
    assert api.post("/research", json={"ticker": "NOPE"}, headers=h1).status_code == 404
    assert api.post("/research", json={"ticker": "TCS", "market": "NYSE"}, headers=h1).status_code == 422
    assert api.post("/research", json={"ticker": "TCS", "period": "forever"}, headers=h1).status_code == 422
    assert api.post("/research", json={"ticker": "TCS", "as_of": "2999-01-01"}, headers=h1).status_code == 422
    assert api.post("/research", json={"ticker": "TCS"}).status_code == 401
    tid = api.post("/research", json={"ticker": "TCS"}, headers=h1).json()["task_id"]
    assert api.get(f"/research/{tid}", headers=h2).status_code == 404
    assert api.get(f"/research/{tid}/report", headers=h2).status_code == 404
    assert api.get("/research", headers=h2).json() == []


def test_replay_request(api):
    h = login(api)
    tid = api.post("/research", json={"ticker": "TCS", "as_of": "2026-07-01"}, headers=h).json()["task_id"]
    d = api.get(f"/research/{tid}", headers=h).json()
    assert d["as_of"] == "2026-07-01" and d["status"] == "partial"      # news skipped in replay
    assert "Replay as of 2026-07-01" in api.get(f"/research/{tid}/report", headers=h).json()["content"]


def test_watchlist_and_preferences(api):
    h = login(api)
    assert api.get("/watchlist", headers=h).json() == []
    assert api.post("/watchlist", json={"ticker": "infy"}, headers=h).status_code == 201
    assert api.post("/watchlist", json={"ticker": "INFY"}, headers=h).status_code == 409
    assert api.post("/watchlist", json={"ticker": "ZZZ"}, headers=h).status_code == 404
    assert api.get("/watchlist", headers=h).json()[0]["name"] == "Infosys"
    assert api.delete("/watchlist/INFY", headers=h).status_code == 204
    assert api.delete("/watchlist/INFY", headers=h).status_code == 404

    assert api.get("/preferences", headers=h).json()["analysis_period"] == "2y"
    assert api.put("/preferences", json={"market": "NSE", "analysis_period": "1y"}, headers=h).status_code == 200
    tid = api.post("/research", json={"ticker": "TCS"}, headers=h).json()["task_id"]
    assert api.get(f"/research/{tid}", headers=h).json()["period"] == "1y"      # preference applied
    assert api.put("/preferences", json={"market": "NYSE"}, headers=h).status_code == 422
