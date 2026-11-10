from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ClaimType(str, Enum):
    FACT = "FACT"
    CALCULATED = "CALCULATED"
    INTERPRETATION = "INTERPRETATION"


class FactEvidence(BaseModel):
    kind: Literal["source"] = "source"
    content_hash: str
    source_url: str | None = None
    quote: str = Field(description="Exact text from the source supporting the claim")


class CalcEvidence(BaseModel):
    kind: Literal["calculation"] = "calculation"
    function: str = Field(description="Name of the tool in app.tools, e.g. 'rsi'")
    inputs: dict
    result: float | dict | None = None


class InterpretationEvidence(BaseModel):
    kind: Literal["interpretation"] = "interpretation"
    supports: list[str] = Field(min_length=1, description="claim_ids of FACT/CALCULATED claims it builds on")


class ClaimDraft(BaseModel):
    """A claim as emitted by an agent, before verification."""

    claim_id: str
    agent: str
    type: ClaimType
    text: str
    evidence: FactEvidence | CalcEvidence | InterpretationEvidence

    @model_validator(mode="after")
    def evidence_matches_type(self):
        expected = {
            ClaimType.FACT: FactEvidence,
            ClaimType.CALCULATED: CalcEvidence,
            ClaimType.INTERPRETATION: InterpretationEvidence,
        }[self.type]
        if not isinstance(self.evidence, expected):
            raise ValueError(f"{self.type.value} claim requires {expected.__name__}")
        return self


class VerifiedClaim(ClaimDraft):
    verified: bool
    verification_note: str | None = None
