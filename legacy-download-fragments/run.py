"""Evaluation harness.

    python -m app.evaluation.run --provider yahoo --news google --out eval_output
    python -m app.evaluation.run --provider synthetic --news synthetic --tickers TCS,INFY,ITC   # harness self-test only

Outputs (in --out): evaluation_report.md, results.json, citation_audit_sample.csv, evaluation.db.
After labelling the `supported` column of the audit CSV (yes / partial / no):
    python -m app.evaluation.run --score-audit eval_output/citation_audit_sample.csv
"""
import argparse
import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.data.universe import UNIVERSE
from app.evaluation import metrics as M
from app.evaluation.drills import run_drills
from app.evaluation.replay import forward_return, score_calls, technical_signal
from app.evaluation.synthetic import SyntheticMarket, SyntheticNews
from app.graph.workflow import Deps
from app.models import EvaluationRun, ResearchTask, User
from app.services.llm import build_llm
from app.services.market_data import YahooProvider, provider_symbol
from app.services.news import build_news_provider
from app.services.research import execute_task


class NoNews:
    name = "none"

    def fetch(self, query, limit=15):
        return []


def _providers(args):
    market = SyntheticMarket() if args.provider == "synthetic" else YahooProvider()
    news = {"synthetic": SyntheticNews, "none": NoNews}.get(args.news, build_news_provider)()
    return market, news


def _make_task(factory, user_id, ticker, as_of=None) -> object:
    with factory() as db:
        t = ResearchTask(user_id=user_id, ticker=ticker, requested_period="2y",
                         as_of_date=datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc) if as_of else None)
        db.add(t); db.commit()
        return t.task_id


def run_evaluation(args) -> dict:
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    db_path = out / "evaluation.db"
    db_path.unlink(missing_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False, "timeout": 60})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    market, news = _providers(args)
    tickers = list(UNIVERSE) if args.tickers == "all" else [t.strip().upper() for t in args.tickers.split(",")]

    with factory() as db:
        user = User(email="evaluation@veritas.local", password_hash="x"); db.add(user); db.commit()
        uid = user.user_id

    def deps():
        return Deps(session_factory=factory, market=market, news=news, llm=build_llm(),
                    max_retries=args.max_retries, backoff_seconds=args.backoff)

    task_ids, wall0 = [], time.perf_counter()
    for i, t in enumerate(tickers, 1):
        tid = _make_task(factory, uid, t)
        execute_task(tid, deps())
        task_ids.append(tid)
        print(f"[{i}/{len(tickers)}] {t} done", flush=True)
        time.sleep(args.pause)

    with factory() as db:
        results = {
            "meta": {"provider": market.name, "news": news.name, "tickers": tickers, "generated_at": datetime.now(timezone.utc).isoformat(),
                     "synthetic": args.provider == "synthetic", "wall_seconds": round(time.perf_counter() - wall0, 1)},
            "calculation_accuracy": M.calculation_accuracy(db, task_ids),
            "citations": M.citation_metrics(db, task_ids),
            "completion_latency": M.completion_and_latency(db, task_ids),
            "cost": M.cost(db, task_ids, args.usd_per_mtok),
            "completeness": M.report_completeness(db, task_ids),
        }
        results["audit_rows"] = M.audit_sample(db, task_ids, args.audit_size, out / "citation_audit_sample.csv")

    print("running failure drills...", flush=True)
    results["drills"] = [d.__dict__ for d in run_drills(market, news, tickers[0])]
    results["replay"] = _replay(args, factory, uid, market, deps, tickers)

    with factory() as db:
        db.add(EvaluationRun(metrics={k: v for k, v in results.items() if k != "drills"}, notes=f"{market.name}/{news.name}"))
        db.commit()
    (out / "results.json").write_text(json.dumps(results, indent=2, default=str))
    (out / "evaluation_report.md").write_text(render_report(results))
    results["db_path"], results["task_ids"] = str(db_path), task_ids
    return results


def _replay(args, factory, uid, market, deps, tickers) -> dict:
    if args.replay_points <= 0:
        return {"skipped": True}
    calls = []
    for t in tickers:
        sym = provider_symbol(t, "NSE")
        df = market.get_ohlcv(sym, "max")
        closes = pd.Series(df["close"].to_numpy(), index=pd.to_datetime(df["date"]))
        last = closes.index[-1].date()
        for k in range(args.replay_points):
            as_of = last - timedelta(days=args.horizon + args.spacing * k)
            ret = forward_return(closes, as_of, args.horizon)
            if ret is None:
                continue
            tid = _make_task(factory, uid, t, as_of)
            execute_task(tid, deps())
            with factory() as db:
                sig = technical_signal(db, tid)
            if sig:
                calls.append((sig, ret))
    return {"signal": "technical", "horizon_days": args.horizon, **score_calls(calls),
            "note": "Fundamental signal not scored: financial statements are not point-in-time."}


def _mark(ok: bool | None) -> str:
    return "n/a" if ok is None else "PASS" if ok else "FAIL"


def render_report(r: dict) -> str:
    ca, ci, cl, co, cp, rp = (r["calculation_accuracy"], r["citations"], r["completion_latency"], r["cost"],
                              r["completeness"], r["replay"])
    lat = cl["latency_ms"]
    L = ["# Veritas Evaluation Report", ""]
    if r["meta"]["synthetic"]:
        L += ["> **SYNTHETIC DATA.** This run validates the evaluation harness only. These numbers are not results.", ""]
    L += [f"Provider: {r['meta']['provider']} · News: {r['meta']['news']} · Tickers: {len(r['meta']['tickers'])} · "
          f"Generated: {r['meta']['generated_at'][:19]} UTC · Wall time: {r['meta']['wall_seconds']}s", "",
          "## Summary", "", "| Metric | Result | Target | Status |", "|---|---|---|---|",
          f"| Calculation accuracy (vs independent reference, tol {ca['tolerance']:g}) | {ca['agreement_percent']}% of {ca['claims_checked']} | 100% | {_mark(ca['agreement_percent'] == 100 and ca['claims_checked'] > 0)} |",
          f"| Citation coverage (FACT claims with a stored source) | {ci['citation_coverage_percent']}% of {ci['fact_claims']} | ≥95% | {_mark(ci['citation_coverage_percent'] >= 95)} |",
          f"| Citation correctness, automated (quote found in source) | {ci['citation_correctness_automated_percent']}% | ≥95% | {_mark(ci['citation_correctness_automated_percent'] >= 95)} |",
          f"| Citation correctness, manual audit | see `citation_audit_sample.csv` ({r['audit_rows']} rows) | label then score | pending |",
          f"| Claims verified by the Verifier | {ci['verified_percent']}% ({ci['claims_verified']}/{ci['claims_total']}) | 100% | {_mark(ci['verified_percent'] == 100)} |",
          f"| Task completion rate (all four agents) | {cl['task_completion_rate_percent']}% | report only | n/a |",
          f"| Usable report rate (completed + partial) | {cl['usable_report_rate_percent']}% | report only | n/a |",
          f"| Report completeness (all required sections) | {cp['complete_percent']}% | 100% | {_mark(cp['complete_percent'] == 100)} |",
          f"| Failure drills passed | {sum(d['passed'] for d in r['drills'])}/{len(r['drills'])} | all | {_mark(all(d['passed'] for d in r['drills']))} |",
          f"| Latency p50 / p95 | {lat['p50'] and round(lat['p50'])} ms / {lat['p95'] and round(lat['p95'])} ms | report only | n/a |",
          f"| Cost per report | {co['tokens_per_report']} tokens, est. ${co['estimated_usd_per_report']} at ${co['usd_per_mtok_assumed']}/Mtok | report only | n/a |", "",
          "## Calculation accuracy", "", "| Function | Agreed | Total |", "|---|---|---|"]
    L += [f"| {k} | {v['agreed']} | {v['total']} |" for k, v in ca["by_function"].items()]
    L += ["", f"Max absolute error: {ca['max_abs_error']:.3g}. Unreferenced functions: {ca['unreferenced']}."]
    if ca["mismatches"]:
        L += ["", "Mismatches:"] + [f"- {m['claim']} {m['function']}: stored {m['stored']} vs reference {m['reference']}" for m in ca["mismatches"]]
    L += ["", "## Claim ledger", "", "| Type | Verified | Total |", "|---|---|---|"]
    L += [f"| {k} | {v['verified']} | {v['total']} |" for k, v in ci["by_type"].items()]
    L += ["", "## Agent reliability", "", f"Status counts: {cl['status_counts']}. Retries used: {cl['retries_total']}.", "",
          "| Agent | Success | p50 latency (ms) |", "|---|---|---|"]
    L += [f"| {k} | {v}% | {round(cl['agent_latency_p50_ms'].get(k) or 0)} |" for k, v in cl["agent_success_percent"].items()]
    L += ["", "## Failure drills", "", "| Drill | Result | Detail |", "|---|---|---|"]
    L += [f"| {d['name']} | {_mark(d['passed'])} | {d['detail']} |" for d in r["drills"]]
    L += ["", "## Replay calibration (technical signal)", ""]
    if rp.get("skipped"):
        L.append("Skipped.")
    else:
        L += [f"Horizon {rp['horizon_days']} days. Windows: {rp['windows']}, directional calls: {rp['directional_calls']}, "
              f"hits: {rp['hits']}, hit rate: {rp['hit_rate_percent']}% (95% CI {rp['hit_rate_ci95']}), "
              f"base rate of up-moves: {rp['base_rate_up_percent']}%.", "",
              "A hit rate is only informative relative to the base rate and its confidence interval. "
              + rp["note"]]
    L += ["", "## Limitations", "",
          "- Small sample (one universe, one time window); replay windows overlap and are not independent.",
          "- Manual citation audit is required to measure whether sources truly support claims; the automated check only confirms the quoted text exists.",
          "- Cost uses the assumed per-million-token rate; the offline template LLM uses zero tokens.",
          "- News sentiment labels are AI-classified from headlines and snippets and are not scored here.", ""]
    return "\n".join(L)


def main(argv=None):
    p = argparse.ArgumentParser(description="Veritas evaluation harness")
    p.add_argument("--provider", choices=["yahoo", "synthetic"], default="yahoo")
    p.add_argument("--news", choices=["google", "synthetic", "none"], default="google")
    p.add_argument("--tickers", default="all")
    p.add_argument("--out", default="eval_output")
    p.add_argument("--audit-size", type=int, default=40)
    p.add_argument("--replay-points", type=int, default=3)
    p.add_argument("--horizon", type=int, default=30)
    p.add_argument("--spacing", type=int, default=30)
    p.add_argument("--usd-per-mtok", type=float, default=0.0)
    p.add_argument("--max-retries", type=int, default=2)
    p.add_argument("--backoff", type=float, default=1.0)
    p.add_argument("--pause", type=float, default=0.0, help="seconds between tickers (rate limiting)")
    p.add_argument("--score-audit", metavar="CSV")
    args = p.parse_args(argv)
    if args.score_audit:
        print(json.dumps(M.score_audit(Path(args.score_audit)), indent=2))
        return
    res = run_evaluation(args)
    print(f"\nReport: {Path(args.out) / 'evaluation_report.md'}")
    print(f"Calculation agreement: {res['calculation_accuracy']['agreement_percent']}% | "
          f"citation coverage: {res['citations']['citation_coverage_percent']}% | "
          f"completion: {res['completion_latency']['task_completion_rate_percent']}% | "
          f"drills passed: {sum(d['passed'] for d in res['drills'])}/{len(res['drills'])}")


if __name__ == "__main__":
    main()
