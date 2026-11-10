"""Claim Ledger verifier. A claim that cannot be verified is blocked from the report.

FACT            -> a source document with that content hash exists for the task and contains the quote.
CALCULATED      -> re-running the registered tool with the stored inputs reproduces the stored result.
INTERPRETATION  -> every supporting claim exists, is FACT/CALCULATED, and is itself verified.
"""
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SourceDocument
from app.schemas.claims import ClaimDraft, ClaimType, VerifiedClaim
from app.tools import run_tool


def _close(a, b, rel=1e-9, abs_=1e-12) -> bool:
    if a is None or b is None:
        return a is b
    if isinstance(a, dict) or isinstance(b, dict):
        return isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys() and all(_close(a[k], b[k]) for k in a)
    return math.isclose(float(a), float(b), rel_tol=rel, abs_tol=abs_)


def verify_claims(db: Session, task_id, claims: list[ClaimDraft]) -> list[VerifiedClaim]:
    excerpts: dict[str, list[str]] = {}
    for d in db.scalars(select(SourceDocument).where(SourceDocument.task_id == task_id)):
        excerpts.setdefault(d.content_hash, []).append(d.content_excerpt or "")
    by_id = {c.claim_id: c for c in claims}
    verdict: dict[str, tuple[bool, str | None]] = {}

    for c in claims:
        if c.type == ClaimType.FACT:
            docs = excerpts.get(c.evidence.content_hash)
            if not docs:
                verdict[c.claim_id] = (False, "No source document with this content hash")
            elif not any(c.evidence.quote in text for text in docs):
                verdict[c.claim_id] = (False, "Quote not found in the source document")
            else:
                verdict[c.claim_id] = (True, None)
        elif c.type == ClaimType.CALCULATED:
            try:
                again = run_tool(c.evidence.function, c.evidence.inputs)
            except Exception as exc:  # unknown tool, bad inputs
                verdict[c.claim_id] = (False, f"Tool re-run failed: {exc}")
                continue
            ok = _close(again, c.evidence.result)
            verdict[c.claim_id] = (ok, None if ok else "Re-computed value differs from the stated value")

    for c in claims:
        if c.type != ClaimType.INTERPRETATION:
            continue
        bad = [s for s in c.evidence.supports
               if s not in by_id or by_id[s].type == ClaimType.INTERPRETATION or not verdict.get(s, (False,))[0]]
        verdict[c.claim_id] = (not bad, None if not bad else f"Unsupported by: {', '.join(bad)}")

    return [VerifiedClaim(**c.model_dump(), verified=verdict[c.claim_id][0],
                          verification_note=verdict[c.claim_id][1]) for c in claims]
