import csv
from argparse import Namespace

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.evaluation import metrics as M
from app.evaluation.reference import reference_value
from app.evaluation.replay import forward_return, score_calls, wilson_interval
from app.evaluation.run import render_report, run_evaluation
from app.models import Claim, ClaimType
from app.tools import run_tool


@pytest.fixture(scope="module")
def evaluation(tmp_path_factory):
    out = tmp_path_factory.mktemp("eval")
    args = Namespace(provider="synthetic", news="synthetic", tickers="TCS,INFY,ITC", out=str(out), audit_size=12,
                     replay_points=2, horizon=30, spacing=30, usd_per_mtok=3.0, max_retries=2, backoff=0.0,
                     pause=0.0)
    return run_evaluation(args), out


def test_reference_agrees_with_tools_on_random_data():
    rng = np.random.default_rng(3)
    v = (100 * np.exp(np.cumsum(rng.normal(0, 0.02, 400)))).tolist()
    cases = [("sma", {"values": v, "window": 50}), ("ema", {"values": v, "window": 26}),
             ("rsi", {"values": v, "period": 14}), ("macd", {"values": v}),
             ("historical_volatility", {"values": v}), ("max_drawdown", {"values": v}), ("total_return", {"values": v}),
             ("growth_rate", {"current": 110.0, "previous": 100.0}), ("cagr", {"begin": 100.0, "end": 150.0, "years": 3}),
             ("margin", {"numerator": 20.0, "revenue": 100.0}), ("debt_to_equity", {"total_debt": 30.0, "total_equity": 80.0}),
             ("roe", {"net_income": 15.0, "equity_end": 80.0, "equity_begin": 70.0}), ("eps", {"net_income": 15.0, "shares": 5.0}),
             ("book_value_per_share", {"total_equity": 80.0, "shares": 5.0}),
             ("pe_ratio", {"price": 60.0, "earnings_per_share": 3.0}), ("pb_ratio", {"price": 60.0, "book_value_ps": 16.0})]
    for fn, inputs in cases:
        assert M._agree(run_tool(fn, inputs), reference_value(fn, inputs)), fn
    with pytest.raises(KeyError):
        reference_value("nope", {})


def test_synthetic_run_passes_all_gates(evaluation):
    res, out = evaluation
    assert res["calculation_accuracy"]["agreement_percent"] == 100.0 and res["calculation_accuracy"]["claims_checked"] > 0
    assert res["calculation_accuracy"]["unreferenced"] == 0 and res["calculation_accuracy"]["max_abs_error"] < 1e-9
    assert res["citations"]["citation_coverage_percent"] == 100.0 and res["citations"]["blocked_claims"] == 0
    assert res["completion_latency"]["task_completion_rate_percent"] == 100.0
    assert res["completeness"]["complete_percent"] == 100.0
    assert all(d["passed"] for d in res["drills"]) and len(res["drills"]) == 5
    assert res["cost"]["tokens_per_report"] == 0
    for name in ("evaluation_report.md", "results.json", "citation_audit_sample.csv", "evaluation.db"):
        assert (out / name).exists()
    assert "SYNTHETIC DATA" in (out / "evaluation_report.md").read_text()


def test_replay_scores_only_observable_windows(evaluation):
    rp = evaluation[0]["replay"]
    assert rp["windows"] > 0 and rp["directional_calls"] <= rp["windows"]
    assert "not point-in-time" in rp["note"]


def test_negative_control_tampered_claim_is_detected(evaluation):
    res, _ = evaluation
    engine = create_engine(f"sqlite:///{res['db_path']}")
    with sessionmaker(bind=engine)() as db:
        claim = db.scalars(select(Claim).where(Claim.claim_type == ClaimType.calculated,
                                               Claim.text.like("14-day RSI%"))).first()
        evidence = dict(claim.evidence)
        evidence["result"] = evidence["result"] + 0.01
        claim.evidence = evidence
        db.flush()
        out = M.calculation_accuracy(db, res["task_ids"])
        db.rollback()
    assert out["agreement_percent"] < 100 and out["mismatches"][0]["function"] == "rsi"
    assert out["max_abs_error"] == pytest.approx(0.01, abs=1e-9)


def test_audit_sheet_and_scoring(evaluation, tmp_path):
    _, out = evaluation
    rows = list(csv.DictReader((out / "citation_audit_sample.csv").open(encoding="utf-8")))
    assert 0 < len(rows) <= 12 and all(r["quote"] and r["source_excerpt"] for r in rows)
    labels = ["yes"] * (len(rows) - 2) + ["partial", "no"]
    path = tmp_path / "labelled.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader()
        for r, lab in zip(rows, labels):
            w.writerow({**r, "supported": lab})
    s = M.score_audit(path)
    assert s["labelled"] == len(rows) and s["yes"] == len(rows) - 2 and s["partial"] == 1 and s["no"] == 1
    assert s["strict_correctness_percent"] < s["lenient_correctness_percent"]
    assert M.score_audit(out / "citation_audit_sample.csv")["labelled"] == 0     # unlabelled rows are ignored


def test_replay_helpers():
    idx = pd.date_range("2026-01-01", periods=100, freq="D")
    closes = pd.Series(np.arange(100.0) + 100, index=idx)
    assert forward_return(closes, "2026-02-01", 30) == pytest.approx(161 / 131 - 1)   # day 31 -> day 61
    assert forward_return(closes, "2026-04-05", 30) is None                  # window extends past the data
    calls = [("bullish", 0.05), ("bullish", -0.02), ("bearish", -0.03), ("neutral", 0.01)]
    s = score_calls(calls)
    assert s["directional_calls"] == 3 and s["hits"] == 2 and s["hit_rate_percent"] == 66.7
    assert s["base_rate_up_percent"] == 50.0
    lo, hi = wilson_interval(2, 3)
    assert lo < 66.7 < hi and wilson_interval(0, 0) is None


def test_report_renders_failures_honestly(evaluation):
    res = dict(evaluation[0])
    res["calculation_accuracy"] = {**res["calculation_accuracy"], "agreement_percent": 90.0,
                                   "mismatches": [{"claim": "technical-3", "function": "rsi", "stored": 1, "reference": 2}]}
    text = render_report(res)
    assert "| FAIL |" in text and "technical-3 rsi" in text
