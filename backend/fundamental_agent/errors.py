from dataclasses import asdict, dataclass


@dataclass
class Reason:
    code: str
    field: str | None
    message: str


class AnalysisError(Exception):
    """Raised when the agent refuses to analyse an input. Carries every reason found."""

    def __init__(self, reasons):
        self.reasons = list(reasons)
        super().__init__("; ".join(r.message for r in self.reasons))

    def to_dict(self):
        return {
            "status": "error",
            "message": "The fundamental analysis could not be completed.",
            "reasons": [asdict(r) for r in self.reasons],
        }
