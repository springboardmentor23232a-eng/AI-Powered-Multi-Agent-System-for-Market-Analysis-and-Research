"""Rule-based financial news sentiment + event detection (Milestone 2).

Deterministic and explainable (no API key, no randomness), so results are reproducible and testable. It is a transparent
baseline: a keyword lexicon with simple negation handling. It can be replaced by an LLM classifier later behind the same
function signature. It reads the HEADLINE (and summary when present) only - it cannot judge nuance or sarcasm.
"""
import re

POSITIVE = {
    "beat", "beats", "surge", "surges", "soar", "soars", "jump", "jumps", "rally", "rallies", "gain", "gains", "growth", "grows",
    "record", "profit", "profits", "profitable", "upgrade", "upgrades", "upgraded", "outperform", "strong", "stronger", "robust",
    "raises", "raised", "boost", "boosts", "expands", "expansion", "wins", "win", "approval", "approved", "dividend", "buyback",
    "optimistic", "recovery", "rebound", "milestone", "partnership", "breakthrough", "tops", "exceeds", "exceeded", "higher",
}
NEGATIVE = {
    "miss", "misses", "missed", "plunge", "plunges", "slump", "slumps", "fall", "falls", "drop", "drops", "decline", "declines",
    "loss", "losses", "cut", "cuts", "downgrade", "downgrades", "downgraded", "underperform", "weak", "weaker", "lawsuit", "sue",
    "sued", "probe", "investigation", "fine", "fined", "penalty", "recall", "layoffs", "layoff", "fraud", "bankruptcy", "default",
    "warning", "warns", "warn", "concern", "concerns", "risk", "risks", "slowdown", "lower", "halt", "halts", "scandal", "ban",
}
NEGATORS = {"not", "no", "never", "without", "fails", "failed", "fail", "unable", "lacks"}
UNCERTAIN = {"may", "might", "could", "reportedly", "rumor", "rumour", "rumors", "unconfirmed", "speculation", "allegedly",
             "sources", "expected", "plans", "considering", "talks"}

EVENT_PATTERNS = {
    "earnings": r"\b(earnings|quarterly|q[1-4]|results|revenue|eps|profit|guidance|outlook)\b",
    "acquisition": r"\b(acqui\w+|merger|merges|takeover|buyout|m&a|stake|divest\w*|spin-?off)\b",
    "regulatory": r"\b(sec|sebi|rbi|fda|ftc|doj|regulator\w*|antitrust|probe|investigation|lawsuit|fine[sd]?|approval|approved|compliance|tariff)\b",
    "dividend": r"\b(dividend|buyback|repurchase)\b",
    "leadership": r"\b(ceo|cfo|chairman|resigns?|appoints?|steps down|succession)\b",
    "product": r"\b(launch\w*|unveil\w*|new product|partnership|contract|deal)\b",
    "workforce": r"\b(layoffs?|job cuts|hiring freeze|restructuring)\b",
}
_WORD = re.compile(r"[a-z][a-z'&-]*")
THRESHOLD = 0.2  # |score| below this = neutral


def classify(text: str) -> dict:
    """-> {sentiment: Positive|Negative|Neutral, score: -1..1, events: [...], uncertain: bool, matched: {pos, neg}}"""
    low = text.lower()
    words = _WORD.findall(low)
    pos = neg = 0
    matched_pos: list[str] = []
    matched_neg: list[str] = []
    for i, w in enumerate(words):
        flipped = any(p in NEGATORS for p in words[max(0, i - 2):i])
        if w in POSITIVE:
            (neg := neg + 1, matched_neg.append("not " + w)) if flipped else (pos := pos + 1, matched_pos.append(w))
        elif w in NEGATIVE:
            (pos := pos + 1, matched_pos.append("not " + w)) if flipped else (neg := neg + 1, matched_neg.append(w))
    total = pos + neg
    score = (pos - neg) / total if total else 0.0
    sentiment = "Positive" if score >= THRESHOLD else "Negative" if score <= -THRESHOLD else "Neutral"
    events = [name for name, pat in EVENT_PATTERNS.items() if re.search(pat, low)]
    return {"sentiment": sentiment, "score": round(score, 2), "events": events,
            "uncertain": any(w in UNCERTAIN for w in words), "matched": {"positive": matched_pos, "negative": matched_neg}}
