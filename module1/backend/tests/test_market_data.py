"""Milestone 1: stock search, OHLCV retrieval, validation, profile, financials, source/timestamp log."""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import inspect, select

from app.database import SessionLocal, engine
from app.models import SourceDocument
from app.validation import Bar, validate_ohlcv

D = date(2026, 1, 5)


def bar(i, o=100, h=105, l=95, c=102, v=1000):
    return Bar(D + timedelta(days=i), o, h, l, c, v)


def good(n=10):
    return [bar(i) for i in range(n)]


# ---------------------------------------------------------------- validation (pure unit tests)
def test_clean_data_passes_untouched():
    rows, rep = validate_ohlcv(good())
    assert len(rows) == 10 and rep["is_clean"] and rep["usable"] and rep["issues"] == [] and rep["rows_removed"] == 0


def test_missing_values_rows_removed_and_reported():
    raw = good() + [Bar(D + timedelta(days=20), 100, None, 95, 102, 10), Bar(D + timedelta(days=21), 100, 105, 95, float("nan"), 10)]
    rows, rep = validate_ohlcv(raw)
    issue = next(i for i in rep["issues"] if i["type"] == "missing_values")
    assert len(rows) == 10 and issue["count"] == 2 and not rep["is_clean"]


def test_duplicate_dates_last_occurrence_wins():
    raw = good() + [bar(3, c=103)]
    rows, rep = validate_ohlcv(raw)
    assert len(rows) == 10
    assert next(r for r in rows if r.date == D + timedelta(days=3)).close == 103
    assert any(i["type"] == "duplicate_dates" and i["count"] == 1 for i in rep["issues"])


@pytest.mark.parametrize("bad", [
    bar(20, h=90, l=95),             # high below low
    bar(20, o=200),                  # open outside the day's range
    bar(20, c=50),                   # close outside the day's range
    bar(20, o=0, h=5, l=0, c=1),     # zero / non-positive price
])
def test_inconsistent_prices_removed(bad):
    rows, rep = validate_ohlcv(good() + [bad])
    assert len(rows) == 10 and any(i["type"] == "inconsistent_prices" for i in rep["issues"])


def test_negative_volume_removed_missing_volume_kept_as_none():
    rows, rep = validate_ohlcv(good() + [bar(20, v=-5), bar(21, v=None)])
    assert len(rows) == 11 and rows[-1].volume is None
    types = {i["type"] for i in rep["issues"]}
    assert {"negative_volume", "missing_volume"} <= types


def test_out_of_order_sorted_and_extreme_move_flagged_not_dropped():
    raw = list(reversed(good())) + [bar(11, o=300, h=320, l=290, c=310)]
    rows, rep = validate_ohlcv(raw)
    assert [r.date for r in rows] == sorted(r.date for r in rows)
    types = {i["type"] for i in rep["issues"]}
    assert "out_of_order" in types and "extreme_price_move" in types and rows[-1].close == 310


def test_too_few_rows_is_not_usable():
    rows, rep = validate_ohlcv(good(3))
    assert not rep["usable"] and any(i["type"] == "insufficient_data" for i in rep["issues"])
    assert validate_ohlcv([])[1]["usable"] is False


# ---------------------------------------------------------------------------- history endpoint
def test_history_returns_ohlcv_source_and_timestamp(user_client):
    r = user_client.get("/api/stocks/NASDAQ/AAPL/history?period=6M")
    assert r.status_code == 200
    j = r.json()
    assert j["ticker"] == "AAPL" and j["currency"] == "USD" and j["period"] == "6M"
    row = j["rows"][0]
    assert set(row) == {"date", "open", "high", "low", "close", "volume"}
    assert all(x["low"] <= x["open"] <= x["high"] and x["low"] <= x["close"] <= x["high"] for x in j["rows"])
    assert j["source"]["synthetic"] is True and "SYNTHETIC" in j["source"]["name"]
    assert datetime.fromisoformat(j["source"]["retrieved_at"])
    assert j["validation"]["usable"] and j["validation"]["rows_valid"] == len(j["rows"])


def test_history_period_controls_length_and_indian_market_currency(user_client):
    n = lambda p: len(user_client.get(f"/api/stocks/NSE/TCS/history?period={p}").json()["rows"])
    assert n("1M") < n("3M") < n("1Y") < n("5Y")
    assert user_client.get("/api/stocks/NSE/TCS/history").json()["currency"] == "INR"


@pytest.mark.parametrize("url", [
    "/api/stocks/NASDAQ/ZZZZZ/history",            # unsupported symbol
    "/api/stocks/NSE/AAPL/history",                # symbol not listed on that market
    "/api/stocks/NASDAQ/AAPL/history?period=10Y",  # unsupported period
    "/api/stocks/LSE/AAPL/history",                # unsupported market
    "/api/stocks/NASDAQ/AAPL.NS/profile",          # bad ticker format
])
def test_market_endpoints_reject_invalid_requests(user_client, url):
    assert user_client.get(url).status_code == 422


@pytest.mark.parametrize("path", ["history", "profile", "financials"])
def test_market_endpoints_require_login(client, path):
    assert client.get(f"/api/stocks/NASDAQ/AAPL/{path}").status_code == 401
    assert client.get("/api/stocks/sources").status_code == 401


def test_profile_lists_missing_fields_and_source(user_client):
    j = user_client.get("/api/stocks/NYSE/JPM/profile").json()
    assert j["profile"]["name"] and j["profile"]["currency"] == "USD" and j["profile"]["sector"]
    assert "market_cap" in j["missing_fields"] and j["profile"]["market_cap"] is None
    assert j["warning"] and j["source"]["synthetic"] and j["source"]["retrieved_at"]


def test_financials_have_four_years_three_statements_and_gaps_reported(user_client):
    f = user_client.get("/api/stocks/NASDAQ/MSFT/financials").json()["financials"]
    assert len(f["periods"]) == 4
    for stmt in ("income_statement", "balance_sheet", "cash_flow"):
        assert all(len(v) == 4 for v in f[stmt].values())
    assert "balance_sheet.cash" in f["missing_metrics"]


# ------------------------------------------------------------------- source / timestamp log
def test_every_retrieval_is_logged_per_user(user_client, make_client):
    user_client.get("/api/stocks/NASDAQ/AAPL/history")
    user_client.get("/api/stocks/NASDAQ/AAPL/profile")
    user_client.get("/api/stocks/NASDAQ/AAPL/financials")
    other = make_client("bob@example.com")
    other.get("/api/stocks/NASDAQ/MSFT/history")
    mine = user_client.get("/api/stocks/sources").json()
    assert {s["doc_type"] for s in mine} == {"ohlcv", "profile", "financials"}
    assert all(s["ticker"] == "AAPL" and s["retrieved_at"] for s in mine)
    ohlcv = next(s for s in mine if s["doc_type"] == "ohlcv")
    assert ohlcv["quality"]["usable"] and ohlcv["record_count"] > 100
    assert [s["ticker"] for s in other.get("/api/stocks/sources").json()] == ["MSFT"]


def test_research_task_records_source_document_and_quality_in_report(user_client):
    tid = user_client.post("/api/research", json={"ticker": "AAPL", "market": "NASDAQ", "analysis_period": "3M"}).json()["task_id"]
    content = user_client.get(f"/api/research/{tid}/report").json()["content"]
    assert content["data_quality"]["usable"] and content["data_retrieved_at"]
    assert {"open", "high", "low", "close", "volume"} <= set(content["price_history"][0])
    with SessionLocal() as db:
        docs = db.scalars(select(SourceDocument).where(SourceDocument.task_id == tid)).all()
    ohlcv = [d for d in docs if d.doc_type == "ohlcv"]
    assert len(ohlcv) == 1 and ohlcv[0].is_synthetic          # prices fetched once and shared by all agents
    assert {d.doc_type for d in docs} <= {"ohlcv", "financials", "news"}   # agents log their own retrievals too


def test_milestone1_schema_has_all_six_tables():
    names = set(inspect(engine).get_table_names())
    assert {"users", "research_tasks", "agent_results", "source_documents", "research_reports", "saved_stocks"} <= names


# ------------------------------------------------------------------------------ Yahoo provider
class _Resp:
    def __init__(self, payload, status=200):
        self._p, self.status_code = payload, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._p


def _use_yahoo(monkeypatch, fake_get):
    from app.config import settings
    import app.market_data as md
    monkeypatch.setattr(settings, "market_data_provider", "yahoo")
    monkeypatch.setattr(md.httpx, "get", fake_get)


def test_yahoo_ohlcv_gaps_and_duplicates_are_caught_by_validation(user_client, monkeypatch):
    t0 = 1_767_571_200  # 2026-01-05
    stamps = [t0 + 86400 * i for i in range(12)] + [t0 + 86400 * 4]          # one duplicated date
    n = len(stamps)
    quote = {"open": [100.0] * n, "high": [105.0] * n, "low": [95.0] * n, "close": [102.0] * n, "volume": [1000] * n}
    quote["close"][2] = None                                                     # missing close
    quote["high"][6], quote["low"][6] = 90.0, 96.0                               # high < low
    payload = {"chart": {"result": [{"timestamp": stamps, "indicators": {"quote": [quote]}}]}}
    _use_yahoo(monkeypatch, lambda *a, **k: _Resp(payload))
    j = user_client.get("/api/stocks/NASDAQ/AAPL/history").json()
    types = {i["type"] for i in j["validation"]["issues"]}
    assert {"missing_values", "duplicate_dates", "inconsistent_prices"} <= types
    assert j["source"]["synthetic"] is False and "Yahoo" in j["source"]["name"]
    assert j["validation"]["rows_received"] == 13 and len(j["rows"]) == 10


def test_provider_failure_returns_502_and_no_invented_data(user_client, monkeypatch):
    _use_yahoo(monkeypatch, lambda *a, **k: (_ for _ in ()).throw(RuntimeError("network down")))
    for path in ("history", "profile", "financials"):
        r = user_client.get(f"/api/stocks/NASDAQ/AAPL/{path}")
        assert r.status_code == 502 and "network down" in r.json()["detail"]


def test_too_little_valid_data_is_rejected_but_still_logged(user_client, monkeypatch):
    t0 = 1_767_571_200
    quote = {"open": [100.0] * 3, "high": [105.0] * 3, "low": [95.0] * 3, "close": [102.0] * 3, "volume": [1] * 3}
    payload = {"chart": {"result": [{"timestamp": [t0, t0 + 86400, t0 + 172800], "indicators": {"quote": [quote]}}]}}
    _use_yahoo(monkeypatch, lambda *a, **k: _Resp(payload))
    assert user_client.get("/api/stocks/NASDAQ/AAPL/history").status_code == 502
    assert user_client.get("/api/stocks/sources").json()[0]["quality"]["usable"] is False


def test_yahoo_financials_parsing(user_client, monkeypatch):
    def series(key, vals):
        return {"meta": {"type": [key]}, key: [{"asOfDate": f"{2022 + i}-03-31", "reportedValue": {"raw": v}} for i, v in enumerate(vals)]}
    payload = {"timeseries": {"result": [series("annualTotalRevenue", [10, 20, 30, 40]), series("annualNetIncome", [1, 2, 3, 4])]}}
    _use_yahoo(monkeypatch, lambda *a, **k: _Resp(payload))
    f = user_client.get("/api/stocks/NASDAQ/AAPL/financials").json()["financials"]
    assert f["periods"][-1] == "2025-03-31" and f["income_statement"]["total_revenue"] == [10, 20, 30, 40]
    assert "balance_sheet.total_assets" in f["missing_metrics"]  # never invented
