import csv
import math
import random
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.evaluation.reference import reference_value
from app.models import AgentResult, Claim, ClaimType, ResearchReport, ResearchTask, SourceDocument, TaskStatus

TOL = 1e-6
REQUIRED_SECTIONS = ["## Summary", "## Fundamental Analysis", "## Technical Analysis", "## News and Sentiment",
                     "## Risk Assessment", "## Conflicting Findings", "## Data Limitations and Uncertainty", "## Sources"]


def _pct(a, b) -> float:
    return round(100 * a / b, 2) if b else 0.0


def _agree(a, b, tol=TOL) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, dict) or isinstance(b, dict):
        return isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys() and all(_agree(a[k], b[k], tol) for k in a)
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tol


def calculation_accuracy(db: Session, task_ids) -> dict:
    claims = db.scalars(select(Claim).where(Claim.task_id.in_(task_ids), Claim.claim_type == ClaimType.calculated)).all()
    by_fn = defaultdict(lambda: [0, 0])
    worst, mismatches, unreferenced = 0.0, [], 0
    for c in claims:
        ev = c.evidence
        try:
            ref = reference_value(ev["function"], ev["inputs"])
        except KeyError:
            unreferenced += 1
            continue
        ok = _agree(ev["result"], ref)
        by_fn[ev["function"]][0] += ok
        by_fn[ev["function"]][1] += 1
        got, exp = (ev["result"], ref)
        for k in (got if isinstance(got, dict) else {"v": None}):
            g, e = (got[k], exp[k]) if isinstance(got, dict) else (got, exp)
            if g is not None and e is not None:
                worst = max(worst, abs(g - e))
        if not ok:
            mismatches.append({"claim": c.ref, "function": ev["function"], "stored": ev["result"], "reference": ref})
    total = sum(v[1] for v in by_fn.values())
    agreed = sum(v[0] for v in by_fn.values())
    return {"claims_checked": total, "agreement_percent": _pct(agreed, total), "max_abs_error": worst,
            "unreferenced": unreferenced, "tolerance": TOL, "mismatches": mismatches[:10],
            "by_function": {k: {"agreed": v[0], "total": v[1]} for k, v in sorted(by_fn.items())}}


def citation_metrics(db: Session, task_ids) -> dict:
    claims = db.scalars(select(Claim).where(Claim.task_id.in_(task_ids))).all()
    docs = defaultdict(list)
    for d in db.scalars(select(SourceDocument).where(SourceDocument.task_id.in_(task_ids))):
        docs[(d.task_id, d.content_hash)].append(d.content_excerpt or "")
    facts = [c for c in claims if c.claim_type == ClaimType.fact]
    with_source = [c for c in facts if (c.task_id, c.evidence["content_hash"]) in docs]
    quote_ok = [c for c in with_source if any(c.evidence["quote"] in t for t in docs[(c.task_id, c.evidence["content_hash"])])]
    verified = sum(c.verified for c in claims)
    by_type = {t.value: {"verified": sum(c.verified for c in claims if c.claim_type == t),
                         "total": sum(1 for c in claims if c.claim_type == t)} for t in ClaimType}
    return {"claims_total": len(claims), "claims_verified": verified, "verified_percent": _pct(verified, len(claims)),
            "fact_claims": len(facts), "citation_coverage_percent": _pct(len(with_source), len(facts)),
            "citation_correctness_automated_percent": _pct(len(quote_ok), len(with_source)),
            "blocked_claims": len(claims) - verified, "by_type": by_type}


def _pctl(xs, q):
    return float(np.percentile(xs, q)) if xs else None


def completion_and_latency(db: Session, task_ids) -> dict:
    tasks = db.scalars(select(ResearchTask).where(ResearchTask.task_id.in_(task_ids))).all()
    status = defaultdict(int)
    for t in tasks:
        status[t.status.value] += 1
    n = len(tasks)
    agents = defaultdict(lambda: defaultdict(int))
    lat = defaultdict(list)
    retries = 0
    for a in db.scalars(select(AgentResult).where(AgentResult.task_id.in_(task_ids))):
        agents[a.agent_name][a.status.value] += 1
        retries += max(0, (a.attempts or 1) - 1)
        if a.latency_ms is not None:
            lat[a.agent_name].append(a.latency_ms)
    totals = [t.latency_ms for t in tasks if t.latency_ms is not None]
    return {"tasks": n, "status_counts": dict(status),
            "task_completion_rate_percent": _pct(status[TaskStatus.completed.value], n),
            "usable_report_rate_percent": _pct(status[TaskStatus.completed.value] + status[TaskStatus.partial.value], n),
            "agent_success_percent": {k: _pct(v.get("success", 0), sum(v.values())) for k, v in sorted(agents.items())},
            "retries_total": retries,
            "latency_ms": {"p50": _pctl(totals, 50), "p95": _pctl(totals, 95), "max": max(totals) if totals else None},
            "agent_latency_p50_ms": {k: _pctl(v, 50) for k, v in sorted(lat.items())}}


def cost(db: Session, task_ids, usd_per_mtok: float) -> dict:
    tokens = [t.tokens_used or 0 for t in db.scalars(select(ResearchTask).where(ResearchTask.task_id.in_(task_ids)))]
    n = len(tokens)
    avg = sum(tokens) / n if n else 0
    return {"tokens_total": sum(tokens), "tokens_per_report": round(avg, 1), "usd_per_mtok_assumed": usd_per_mtok,
            "estimated_usd_per_report": round(avg / 1e6 * usd_per_mtok, 6)}


def report_completeness(db: Session, task_ids) -> dict:
    reports = db.scalars(select(ResearchReport).where(ResearchReport.task_id.in_(task_ids))).all()
    full = sum(all(s in r.report_content for s in REQUIRED_SECTIONS) for r in reports)
    return {"reports": len(reports), "complete_percent": _pct(full, len(reports)), "required_sections": REQUIRED_SECTIONS}


def audit_sample(db: Session, task_ids, n: int, path: Path, seed: int = 7) -> int:
    """Write a sample of FACT claims with their sources for manual labelling (`supported` = yes / partial / no)."""
    tasks = {t.task_id: t.ticker for t in db.scalars(select(ResearchTask).where(ResearchTask.task_id.in_(task_ids)))}
    docs = {(d.task_id, d.content_hash): d for d in db.scalars(select(SourceDocument).where(SourceDocument.task_id.in_(task_ids)))}
    facts = [c for c in db.scalars(select(Claim).where(Claim.task_id.in_(task_ids), Claim.claim_type == ClaimType.fact))]
    news = [c for c in facts if c.agent_name == "news"]
    other = [c for c in facts if c.agent_name != "news"]
    rnd = random.Random(seed)
    pick = rnd.sample(news, min(len(news), n * 3 // 4)) + rnd.sample(other, min(len(other), n - min(len(news), n * 3 // 4)))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "claim_id", "agent", "claim_text", "quote", "source_type", "source_url", "source_excerpt", "supported"])
        for c in pick:
            d = docs.get((c.task_id, c.evidence["content_hash"]))
            w.writerow([tasks[c.task_id], c.ref, c.agent_name, c.text, c.evidence["quote"], d.source_type if d else "",
                        d.source_url if d else "", (d.content_excerpt if d else "")[:400], ""])
    return len(pick)


def score_audit(path: Path) -> dict:
    rows = [r for r in csv.DictReader(path.open(encoding="utf-8")) if r["supported"].strip()]
    counts = {k: sum(r["supported"].strip().lower() == k for r in rows) for k in ("yes", "partial", "no")}
    n = len(rows)
    return {"labelled": n, **counts, "strict_correctness_percent": _pct(counts["yes"], n),
            "lenient_correctness_percent": _pct(counts["yes"] + counts["partial"], n)}
