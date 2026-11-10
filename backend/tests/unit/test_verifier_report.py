from datetime import datetime, timezone

from app.models import ResearchTask, SourceDocument, User
from app.schemas.agents import AgentResult, AgentStatus
from app.schemas.claims import CalcEvidence, ClaimDraft, ClaimType, FactEvidence, InterpretationEvidence
from app.services.report import build_report, evidence_score
from app.services.verifier import verify_claims


def make_task(db):
    u = User(email="u@x.com", password_hash="x"); db.add(u); db.commit()
    t = ResearchTask(user_id=u.user_id, ticker="TCS"); db.add(t); db.commit()
    db.add(SourceDocument(task_id=t.task_id, source_type="news", title="t", content_hash="h1",
                          content_excerpt="TCS profit rises sharply"))
    db.commit()
    return t


def claims():
    return [
        ClaimDraft(claim_id="a-1", agent="a", type=ClaimType.FACT, text="good fact",
                   evidence=FactEvidence(content_hash="h1", quote="profit rises")),
        ClaimDraft(claim_id="a-2", agent="a", type=ClaimType.FACT, text="bad quote",
                   evidence=FactEvidence(content_hash="h1", quote="profit collapses")),
        ClaimDraft(claim_id="a-3", agent="a", type=ClaimType.FACT, text="no source",
                   evidence=FactEvidence(content_hash="zzz", quote="x")),
        ClaimDraft(claim_id="a-4", agent="a", type=ClaimType.CALCULATED, text="margin",
                   evidence=CalcEvidence(function="margin", inputs={"numerator": 20, "revenue": 100}, result=0.2)),
        ClaimDraft(claim_id="a-5", agent="a", type=ClaimType.CALCULATED, text="tampered",
                   evidence=CalcEvidence(function="margin", inputs={"numerator": 20, "revenue": 100}, result=0.9)),
        ClaimDraft(claim_id="a-6", agent="a", type=ClaimType.CALCULATED, text="unknown tool",
                   evidence=CalcEvidence(function="nope", inputs={}, result=1.0)),
        ClaimDraft(claim_id="a-7", agent="a", type=ClaimType.INTERPRETATION, text="ok interp",
                   evidence=InterpretationEvidence(supports=["a-1", "a-4"])),
        ClaimDraft(claim_id="a-8", agent="a", type=ClaimType.INTERPRETATION, text="built on bad claim",
                   evidence=InterpretationEvidence(supports=["a-1", "a-5"])),
        ClaimDraft(claim_id="a-9", agent="a", type=ClaimType.INTERPRETATION, text="dangling",
                   evidence=InterpretationEvidence(supports=["missing"])),
        ClaimDraft(claim_id="a-10", agent="a", type=ClaimType.INTERPRETATION, text="interp on interp",
                   evidence=InterpretationEvidence(supports=["a-7"])),
    ]


def test_verifier_blocks_unsupported_claims(db):
    t = make_task(db)
    out = {c.claim_id: c for c in verify_claims(db, t.task_id, claims())}
    assert [k for k, v in out.items() if v.verified] == ["a-1", "a-4", "a-7"]
    assert "Quote not found" in out["a-2"].verification_note
    assert "No source document" in out["a-3"].verification_note
    assert "differs" in out["a-5"].verification_note
    assert "Tool re-run failed" in out["a-6"].verification_note
    assert "Unsupported by" in out["a-8"].verification_note


def test_report_contains_only_verified_claims_and_marks_unavailable(db):
    t = make_task(db)
    vc = verify_claims(db, t.task_id, claims())
    results = {
        "fundamental": AgentResult(agent="fundamental", status=AgentStatus.success, data={"signal": "bullish"}),
        "news": AgentResult(agent="news", status=AgentStatus.unavailable, error="news down",
                            limitations=["news data could not be retrieved"]),
    }
    for c in vc:
        c.agent = "fundamental"
    rep = build_report(ticker="TCS", market="NSE", period="2y", as_of=None,
                       generated_at=datetime(2026, 11, 2, tzinfo=timezone.utc), results=results, claims=vc,
                       contradictions=[], sources=[], company_name="Tata Consultancy Services")
    text = rep["content"]
    assert "good fact" in text and "**20.00%**" in text and "ok interp" in text
    for blocked in ("bad quote", "no source", "tampered", "unknown tool", "built on bad claim", "dangling"):
        assert blocked not in text
    assert "> **Unavailable.** news down" in text
    assert "7 claim(s) failed verification" in rep["limitations"]
    assert rep["score"] == evidence_score(vc) and rep["score"]["verified"] == 3
    assert "not investment advice" in text
