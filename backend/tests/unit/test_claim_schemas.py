import pytest
from pydantic import ValidationError

from app.schemas.claims import CalcEvidence, ClaimDraft, ClaimType, FactEvidence, InterpretationEvidence


def test_valid_claims():
    ClaimDraft(claim_id="c1", agent="news", type=ClaimType.FACT, text="x",
               evidence=FactEvidence(content_hash="h", quote="q"))
    ClaimDraft(claim_id="c2", agent="technical", type=ClaimType.CALCULATED, text="RSI is 61",
               evidence=CalcEvidence(function="rsi", inputs={"period": 14}, result=61.0))
    ClaimDraft(claim_id="c3", agent="risk", type=ClaimType.INTERPRETATION, text="y",
               evidence=InterpretationEvidence(supports=["c1", "c2"]))


def test_evidence_must_match_type():
    with pytest.raises(ValidationError):
        ClaimDraft(claim_id="c1", agent="a", type=ClaimType.FACT, text="x",
                   evidence=CalcEvidence(function="rsi", inputs={}))


def test_interpretation_needs_support():
    with pytest.raises(ValidationError):
        InterpretationEvidence(supports=[])
