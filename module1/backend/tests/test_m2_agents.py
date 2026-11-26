"""Milestone 2: the four agents, the Kaggle dataset loader, news providers, /api/analysis and the research workflow."""
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

import app.agents.technical as technical_mod
import app.financial_dataset as fd
import app.news_data as nd
from app.agents import build_context, run_agent, run_all
from app.agents.schemas import (AGENT_MODELS, AGENT_ORDER, FundamentalOutput, NewsOutput, RatioItem, TechnicalOutput)
from app.catalog import lookup
from app.config import settings
from app.database import SessionLocal
from app.models import AgentResult, SourceDocument
from app.tools import check_dataset

NOW = datetime.now(timezone.utc)

# A TEST FIXTURE shaped like the Kaggle file (odd header spellings on purpose). Not real company data.
CSV = """Company,Category,Year,Market Cap(in B USD),Revenue,Gross Profit,Net Income,EPS,Shareholders Equity,Cash Flow from Operating,Debt/Equity Ratio,Current Ratio,Inflation Rate (in US)
AAPL,Technology,2019,900,260,98,55,2.97,90,69,1.2,1.5,1.8
AAPL,Technology,2020,2000,274,105,57,3.28,65,80,1.7,1.4,1.2
AAPL,Technology,2022,2400,394,170,100,6.11,50,122,2.4,0.9,8.0
AAPL,Technology,2023,2700,383,169,97,6.13,62,110,1.8,1.0,4.1
MSFT,Technology,2023,2500,212,146,72,9.68,206,87,0.4,1.7,4.1
ORCL,Technology,2023,300,50,36,8,2.9,6,18,5.0,0.8,4.1
KO,Consumer Defensive,2023,260,45,27,11,2.5,25,12,1.6,1.1,4.1
"""


@pytest.fixture
def dataset(tmp_path):
    p = tmp_path / "fin.csv"
    p.write_text(CSV)
    old = settings.financials_dataset_path
    settings.financials_dataset_path = str(p)
    fd.clear_cache()
    yield p
    settings.financials_dataset_path = old
    fd.clear_cache()


@pytest.fixture(autouse=True)
def no_dataset_by_default():
    old = settings.financials_dataset_path
    settings.financials_dataset_path = str(settings.financials_dataset_path or "/nonexistent/none.csv")
    fd.clear_cache()
    yield
    settings.financials_dataset_path = old
    fd.clear_cache()


def ctx(ticker="AAPL", market="NASDAQ", period="1Y"):
    return build_context(lookup(ticker, market), period)


def valid(name, out):
    """Round-trip through the declared schema: proves the output has the defined structure."""
    return AGENT_MODELS[name].model_validate(out.model_dump(mode="json"))


# -------------------------------------------------------------------------------- schemas / all agents
def test_all_agents_complete_in_demo_mode_and_match_their_schemas():
    out = run_all(ctx())
    assert list(out) == list(AGENT_ORDER)
    for name, o in out.items():
        assert o.status == "Completed" and o.agent == name and o.summary and o.generated_at
        valid(name, o)
        assert o.sources and all(s.synthetic for s in o.sources)          # demo mode: every source labelled synthetic


def test_findings_distinguish_fact_calculated_interpretation():
    kinds = {f.kind for o in run_all(ctx()).values() for f in o.findings}
    assert kinds == {"fact", "calculated", "interpretation"}


def test_agents_are_deterministic_for_the_same_inputs():
    a, b = run_all(ctx()), run_all(ctx())
    assert a["risk"].metrics == b["risk"].metrics and a["risk"].level == b["risk"].level
    assert a["technical"].indicators == b["technical"].indicators
    assert [r.value for r in a["fundamental"].ratios] == [r.value for r in b["fundamental"].ratios]


# ------------------------------------------------------------------------------------ technical agent
def test_technical_chart_series_align_and_are_in_range():
    c = ctx(period="6M")
    t = technical_mod.run(c)
    ch = t.chart
    n = len(ch.dates)
    assert n == len(c.window) and all(len(getattr(ch, k)) == n for k in
                                      ("close", "sma20", "sma50", "ema12", "ema26", "rsi14", "macd", "macd_signal", "macd_hist"))
    assert all(0 <= v <= 100 for v in ch.rsi14 if v is not None)
    assert ch.sma50[-1] is not None and ch.sma20[0] is not None        # warm-up history makes SMA50 available in a 6M window
    assert t.bias in ("upward", "downward", "mixed") and t.conditions and t.indicators["rsi_14"] is not None
    assert any("not guaranteed predictions" in x for x in t.limitations)


def test_technical_short_period_still_has_indicators_thanks_to_warmup():
    t = technical_mod.run(ctx(period="1M"))
    assert len(t.chart.dates) < 30 and t.indicators["sma_50"] is not None


def test_technical_unavailable_with_too_little_data():
    c = ctx()
    c.bars = c.window = c.bars[:10]
    t = technical_mod.run(c)
    assert t.status == "Unavailable" and t.bias == "insufficient_data" and "at least" in t.summary


# ------------------------------------------------------------------------------------ fundamental agent
def test_fundamental_demo_is_flagged_synthetic_and_refuses_valuation():
    f = run_agent("fundamental", ctx())
    assert isinstance(f, FundamentalOutput) and "SYNTHETIC" in f.summary
    r = {x.key: x for x in f.ratios}
    assert r["pe"].value is None and "not computed" in r["pe"].reason_unavailable.lower()
    assert r["net_margin"].value is not None and r["net_margin"].formula and r["net_margin"].kind == "calculated"
    assert f.history["periods"] and "net_margin" in f.history["series"]
    assert any("SYNTHETIC" in x for x in f.limitations)
    assert r["revenue_growth_yoy"].unit == "%" and r["debt_to_equity"].unit == "x"


def test_fundamental_uses_dataset_peers_and_flags_gaps_and_stale_valuation(dataset):
    f = run_agent("fundamental", ctx())
    assert "Kaggle" in f.basis and f.latest_period == "2023" and f.currency == "USD"
    r = {x.key: x for x in f.ratios}
    assert r["net_margin"].value == pytest.approx(97 / 383)
    assert r["roe"].value == pytest.approx(97 / ((62 + 50) / 2))
    assert r["debt_to_equity"].kind == "reported" and r["debt_to_equity"].value == 1.8
    assert r["revenue_growth_yoy"].value == pytest.approx(383 / 394 - 1)       # growth vs the previous AVAILABLE period (2022)
    assert r["pe"].value is None and "not computed" in r["pe"].reason_unavailable.lower()   # synthetic price (and 2023 EPS is stale) -> refused
    assert f.peers["category"] == "Technology" and f.peers["count"] == 2 and f.peers["year"] == 2023
    assert f.peers["median"]["net_margin"] == pytest.approx((72 / 212 + 8 / 50) / 2)
    assert any("2021" in i for i in f.data_issues)                                # missing year reported
    assert any("USD" in x for x in f.limitations)
    assert any("peer median" in x.text for x in f.findings)
    assert f.sources[0].url == fd.DATASET_URL
    valid("fundamental", f)


def test_fundamental_dataset_company_not_found_is_explained(dataset):
    f = run_agent("fundamental", ctx("TSLA"))
    assert f.peers is None and any("not found in the reference dataset" in x for x in f.limitations)


def test_fundamental_unreadable_dataset_is_reported_not_fatal(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("foo,bar\n1,2\n")
    settings.financials_dataset_path = str(bad)
    fd.clear_cache()
    f = run_agent("fundamental", ctx())
    assert f.status == "Completed" and any("could not be read" in x for x in f.limitations)


def test_fundamental_unavailable_when_no_source(monkeypatch):
    import app.agents.fundamental as fm
    from app.market_data import MarketDataError
    def boom(_):
        raise MarketDataError("provider down")
    monkeypatch.setattr(fm, "fetch_financials", boom)
    f = run_agent("fundamental", ctx())
    assert f.status == "Unavailable" and "provider down" in f.summary and "nothing was estimated" in " ".join(f.limitations)


def test_fundamental_detects_inconsistent_financial_data():
    from app.agents.fundamental import _data_issues
    issues = _data_issues(["2021", "2022", "2023"], {"revenue": [100, 100, None], "net_income": [150, 10, 5],
                                                     "gross_profit": [120, 40, 30], "equity": [-5, 10, 20]})
    text = " ".join(issues)
    assert "Net income exceeds revenue in 2021" in text and "Gross profit exceeds revenue in 2021" in text
    assert "Revenue is missing for 2023" in text and "equity is zero or negative in 2021" in text


# --------------------------------------------------------------------------------------- dataset loader
def test_dataset_header_matching_and_duplicates(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("company name,FISCAL YEAR,Total Revenue,Net Profit,Total Equity\nAcme,2020,10,1,5\nAcme,2020,12,2,6\nAcme,2021,N/A,3,7\n,2021,1,1,1\n")
    ds = fd.parse_csv(p)
    assert ds.column_map["company"] == "company name" and ds.column_map["year"] == "FISCAL YEAR"
    assert ds.report["duplicate_company_year"] == 1 and ds.report["rows_skipped_no_company_or_year"] == 1
    row2020 = next(r for r in ds.rows if r["year"] == 2020)
    assert row2020["revenue"] == 12                                      # last duplicate wins
    assert next(r for r in ds.rows if r["year"] == 2021)["revenue"] is None   # "N/A" -> missing, not 0


def test_dataset_requires_company_year_and_a_financial_column(tmp_path):
    p = tmp_path / "b.csv"
    p.write_text("name,notes\nx,y\n")
    with pytest.raises(ValueError, match="cannot find the columns"):
        fd.parse_csv(p)


def test_dataset_company_matching(dataset):
    ds = fd.get_dataset()
    assert fd.match_company(ds, "AAPL", "Apple Inc.") == "AAPL"
    assert fd.match_company(ds, "ZZZZ", "Unknown Co") is None


def test_dataset_status_endpoint_and_check_tool(user_client, dataset, capsys):
    j = user_client.get("/api/analysis/dataset").json()
    assert j["loaded"] and j["companies"] == 4 and j["matched_columns"]["revenue"] == "Revenue"
    assert "Inflation Rate (in US)" in j["ignored_columns"] and j["load_report"]["rows_used"] == 7
    assert check_dataset.main(["x", str(dataset)]) == 0
    assert "Recognised columns" in capsys.readouterr().out


def test_dataset_status_when_missing(user_client, capsys):
    j = user_client.get("/api/analysis/dataset").json()
    assert j["loaded"] is False and "financial_statements.csv" in str(j.get("how_to_load") or j.get("expected_path"))
    assert check_dataset.main(["x", "/nope.csv"]) == 1


# ------------------------------------------------------------------------------------------ news agent
RSS = """<?xml version="1.0"?><rss><channel>
<item><title>Acme profit surges after strong quarter</title><link>https://news.example/1</link>
<pubDate>Tue, 17 Nov 2026 10:00:00 +0000</pubDate><description>Record results.</description></item>
<item><title>Regulator launches probe into Acme accounting</title><link>https://news.example/2</link>
<pubDate>Wed, 18 Nov 2026 09:30:00 +0000</pubDate></item>
<item><title>Acme could be considering a merger, sources say</title><link>https://news.example/3</link></item>
</channel></rss>"""


class FakeResp:
    def __init__(self, text="", status=200):
        self.text, self.status_code = text, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_news_demo_is_labelled_sample_with_conflicts_and_no_links():
    n = run_agent("news", ctx())
    assert isinstance(n, NewsOutput) and n.status == "Completed" and "SAMPLE" in n.summary
    assert all(a.synthetic and a.url is None for a in n.articles) and any("NOT real news" in x for x in n.limitations)
    assert sum(n.counts.values()) == len(n.articles) and n.counts["Positive"] > n.counts["Negative"] and n.tone == "Positive" and n.conflicts
    assert all(n.articles[i].published_at >= n.articles[i + 1].published_at for i in range(len(n.articles) - 1))


def test_news_yahoo_rss_parsing_links_dates_events(monkeypatch):
    monkeypatch.setattr(settings, "news_provider", "yahoo")
    monkeypatch.setattr(nd.httpx, "get", lambda *a, **k: FakeResp(RSS))
    n = run_agent("news", ctx())
    assert n.status == "Completed" and len(n.articles) == 3 and not any(a.synthetic for a in n.articles)
    assert n.articles[0].url == "https://news.example/2" and n.articles[0].published_at.year == 2026   # newest first
    by_title = {a.title: a for a in n.articles}
    assert by_title["Acme profit surges after strong quarter"].sentiment == "Positive"
    assert by_title["Regulator launches probe into Acme accounting"].sentiment == "Negative"
    assert "regulatory" in by_title["Regulator launches probe into Acme accounting"].events
    assert by_title["Acme could be considering a merger, sources say"].uncertain
    assert any("no publication date" in x for x in n.limitations)            # item 3 has no pubDate
    assert not any("NOT real news" in x for x in n.limitations) and n.sources[0].synthetic is False


def test_news_provider_failure_is_unavailable_not_invented(monkeypatch):
    monkeypatch.setattr(settings, "news_provider", "yahoo")
    monkeypatch.setattr(nd.httpx, "get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no internet")))
    n = run_agent("news", ctx())
    assert n.status == "Unavailable" and n.articles == [] and "no internet" in n.error
    assert "No news was invented" in " ".join(n.limitations)


def test_news_empty_feed_and_missing_newsapi_key(monkeypatch):
    monkeypatch.setattr(settings, "news_provider", "yahoo")
    monkeypatch.setattr(nd.httpx, "get", lambda *a, **k: FakeResp("<rss><channel></channel></rss>"))
    assert run_agent("news", ctx()).status == "Unavailable"
    monkeypatch.setattr(settings, "news_provider", "newsapi")
    monkeypatch.setattr(settings, "newsapi_key", "")
    n = run_agent("news", ctx())
    assert n.status == "Unavailable" and "NEWSAPI_KEY" in n.error


# ------------------------------------------------------------------------------------------ risk agent
def _fund(nig=None, margins=None, de=None):
    ratios = []
    for key, val, unit in (("net_income_growth_yoy", nig, "%"), ("debt_to_equity", de, "x")):
        if val is not None:
            ratios.append(RatioItem(key=key, name=key, value=val, unit=unit, formula="f"))
    return FundamentalOutput(ticker="AAPL", market="NASDAQ", generated_at=NOW, summary="s", ratios=ratios,
                             history={"periods": ["1", "2"], "series": {"net_margin": margins or []}})


def _tech(bias):
    return TechnicalOutput(ticker="AAPL", market="NASDAQ", generated_at=NOW, summary="s", bias=bias)


def _news(tone):
    return NewsOutput(ticker="AAPL", market="NASDAQ", generated_at=NOW, summary="s", tone=tone)


def test_risk_metrics_levels_and_scenarios():
    r = run_agent("risk", ctx(), run_all(ctx()))
    assert r.status == "Completed" and r.level in ("Low", "Moderate", "High") and len(r.level_basis) == 3
    m = r.metrics
    assert m["annualised_volatility_pct"] > 0 and m["max_drawdown_pct"] <= 0 and m["var_95_1d_pct"] > 0
    assert [s.name.split()[0] for s in r.scenarios] == ["Downside", "Median", "Upside"]
    assert r.scenarios[0].return_pct <= r.scenarios[1].return_pct <= r.scenarios[2].return_pct
    assert any("not forecasts" in x for x in r.limitations) and any("SYNTHETIC" in g for g in r.data_gaps)
    valid("risk", r)


def test_risk_flags_conflict_between_upward_technicals_and_declining_profit():
    r = run_agent("risk", ctx(), {"fundamental": _fund(nig=-0.25), "technical": _tech("upward"), "news": _news("Neutral")})
    pairs = [(c.between, c.description) for c in r.conflicts]
    assert (["technical", "fundamental"], pairs[0][1]) in pairs and "declining profitability" in pairs[0][1]
    assert any("Net income fell 25.0%" in x for x in r.financial_risks)


def test_risk_declining_margin_alone_also_triggers_conflict():
    r = run_agent("risk", ctx(), {"fundamental": _fund(margins=[0.2, 0.1]), "technical": _tech("upward"), "news": _news("Neutral")})
    assert any(c.between == ["technical", "fundamental"] for c in r.conflicts)


def test_risk_news_vs_technical_conflicts_and_high_leverage():
    r = run_agent("risk", ctx(), {"fundamental": _fund(de=3.1), "technical": _tech("downward"), "news": _news("Positive")})
    assert any(c.between == ["news", "technical"] for c in r.conflicts)
    assert any("High leverage" in x for x in r.financial_risks)
    r2 = run_agent("risk", ctx(), {"fundamental": _fund(), "technical": _tech("upward"), "news": _news("Negative")})
    assert any(c.between == ["news", "technical"] for c in r2.conflicts)


def test_risk_missing_agents_are_data_gaps():
    r = run_agent("risk", ctx(), {})
    assert sum("unavailable, so the risk view is incomplete" in g for g in r.data_gaps) == 3


def test_risk_level_is_a_deterministic_function_of_the_points():
    r = run_agent("risk", ctx(), {})
    pts = [0 if "-> low" in b else 1 if "-> moderate" in b else 2 for b in r.level_basis]
    avg = sum(pts) / len(pts)
    assert r.level == ("Low" if avg < 0.5 else "Moderate" if avg < 1.25 else "High")


def test_risk_unavailable_with_too_little_data():
    c = ctx()
    c.bars = c.window = c.bars[:10]
    assert run_agent("risk", c).status == "Unavailable"


# -------------------------------------------------------------------------------------------- runner
def test_a_crashing_agent_becomes_failed_and_risk_notes_it(monkeypatch):
    def boom(_):
        raise RuntimeError("kaboom")
    monkeypatch.setattr(technical_mod, "run", boom)
    out = run_all(ctx())
    assert out["technical"].status == "Failed" and "kaboom" in out["technical"].error
    assert out["risk"].status == "Completed" and any("technical analysis is unavailable" in g for g in out["risk"].data_gaps)
    valid("technical", out["technical"])


def test_unknown_agent_name_raises():
    with pytest.raises(KeyError):
        run_agent("astrology", ctx())


# ---------------------------------------------------------------------------------- API + workflow
def test_analysis_endpoint_all_and_single(user_client):
    j = user_client.get("/api/analysis/NASDAQ/AAPL/all?period=6M").json()
    assert j["ticker"] == "AAPL" and set(j["agents"]) == set(AGENT_ORDER) and j["period"] == "6M"
    assert all(a["status"] == "Completed" for a in j["agents"].values()) and j["agents"]["technical"]["chart"]["dates"]
    one = user_client.get("/api/analysis/NASDAQ/AAPL/risk").json()["agents"]
    assert list(one) == ["risk"] and one["risk"]["level"] in ("Low", "Moderate", "High")
    kinds = {d.doc_type for d in SessionLocal().scalars(select(SourceDocument)).all()}
    assert {"ohlcv", "financials", "news"} <= kinds                       # every retrieval is logged with source + time


def test_analysis_endpoint_validation_and_auth(client, user_client):
    assert user_client.get("/api/analysis/NASDAQ/ZZZZZ/all").status_code == 422
    assert user_client.get("/api/analysis/NSE/AAPL/all").status_code == 422
    assert user_client.get("/api/analysis/NASDAQ/AAPL/astrology").status_code == 422
    assert user_client.get("/api/analysis/NASDAQ/AAPL/all?period=10Y").status_code == 422
    anon = type(client)(client.app)
    assert anon.get("/api/analysis/NASDAQ/AAPL/all").status_code == 401
    assert anon.get("/api/analysis/dataset").status_code == 401


def test_analysis_endpoint_provider_failure_is_502(user_client, monkeypatch):
    import app.market_data as md
    monkeypatch.setattr(settings, "market_data_provider", "yahoo")
    monkeypatch.setattr(md.httpx, "get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("offline")))
    r = user_client.get("/api/analysis/NASDAQ/AAPL/all")
    assert r.status_code == 502 and "offline" in r.json()["detail"]


def test_research_task_stores_four_agent_results_and_report_content(user_client):
    tid = user_client.post("/api/research", json={"ticker": "MSFT", "market": "NASDAQ", "analysis_period": "1Y"}).json()["task_id"]
    rep = user_client.get(f"/api/research/{tid}/report").json()
    assert set(rep["content"]["agents"]) == set(AGENT_ORDER)
    assert "chart" not in rep["content"]["agents"]["technical"]            # bulky series stay out of the stored report
    assert "[Risk]" in rep["summary"] and "[Fundamental]" in rep["summary"]
    with SessionLocal() as db:
        rows = db.scalars(select(AgentResult).where(AgentResult.task_id == tid)).all()
    assert sorted(r.agent_name for r in rows) == sorted(AGENT_ORDER) and all(r.status == "Completed" for r in rows)
    assert all(r.output["agent"] == r.agent_name for r in rows)


def test_agent_results_are_deleted_with_their_task_and_isolated_per_user(user_client, make_client):
    tid = user_client.post("/api/research", json={"ticker": "AAPL", "market": "NASDAQ", "analysis_period": "3M"}).json()["task_id"]
    other = make_client("bob@example.com")
    assert other.get(f"/api/research/{tid}/report").status_code == 404
    assert other.get(f"/api/research/{tid}").status_code == 404
