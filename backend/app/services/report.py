"""Report Generation Agent. Deterministic assembly: only verified claims are printed, and every line is
tagged FACT / CALC / AI so a reader can tell data, computation and interpretation apart."""
from datetime import datetime

from app.schemas.agents import AgentResult, AgentStatus
from app.schemas.claims import ClaimType, VerifiedClaim

TAG = {ClaimType.FACT: "FACT", ClaimType.CALCULATED: "CALC", ClaimType.INTERPRETATION: "AI"}
PCT_FUNCS = {"growth_rate", "cagr", "margin", "roe", "historical_volatility", "max_drawdown", "total_return"}
SECTIONS = [("fundamental", "Fundamental Analysis"), ("technical", "Technical Analysis"),
            ("news", "News and Sentiment"), ("risk", "Risk Assessment")]


def format_calc(function: str, result) -> str:
    if isinstance(result, dict):
        return ", ".join(f"{k} {v:,.3f}" for k, v in result.items() if v is not None)
    if result is None:
        return "n/a"
    return f"{result * 100:.2f}%" if function in PCT_FUNCS else f"{result:,.2f}"


def evidence_score(claims: list[VerifiedClaim], blocked: int | None = None) -> dict:
    total = len(claims)
    ok = sum(c.verified for c in claims)
    return {"total": total, "verified": ok, "blocked": total - ok,
            "percent": round(100 * ok / total, 1) if total else 0.0}


def _line(c: VerifiedClaim) -> str:
    text = c.text
    if c.type == ClaimType.CALCULATED:
        text = f"{c.text}: **{format_calc(c.evidence.function, c.evidence.result)}**"
    return f"- {text} `[{TAG[c.type]} · {c.claim_id}]`"


def build_report(*, ticker: str, market: str, period: str, as_of, generated_at: datetime,
                 results: dict[str, AgentResult], claims: list[VerifiedClaim], contradictions: list,
                 sources: list, company_name: str | None = None) -> dict:
    verified = [c for c in claims if c.verified]
    score = evidence_score(claims)
    signals = {n: r.data.get("signal") for n, r in results.items() if r.status == AgentStatus.success and "signal" in r.data}
    limitations: list[str] = []
    for n, r in results.items():
        limitations += [f"[{n}] {l}" for l in r.limitations]
        if r.status != AgentStatus.success:
            limitations.append(f"[{n}] section unavailable" + (f": {r.error}" if r.error else ""))
    if score["blocked"]:
        limitations.append(f"{score['blocked']} claim(s) failed verification and were excluded from this report")

    sig_text = ", ".join(f"{n} {s}" for n, s in signals.items()) or "no signals available"
    summary = (f"Signals: {sig_text}. {len(contradictions)} contradiction(s) between agents. "
               f"{score['verified']} of {score['total']} claims verified.")

    title = f"{company_name} ({ticker})" if company_name else ticker
    md = [f"# Research Report: {title}", "",
          f"Market: {market} · Period: {period} · Generated: {generated_at:%Y-%m-%d %H:%M} UTC"
          + (f" · **Replay as of {as_of}**" if as_of else ""), "",
          f"**Evidence score: {score['verified']}/{score['total']} claims verified ({score['percent']}%)**", "",
          "Legend: `FACT` = sourced data · `CALC` = reproducible computation · `AI` = interpretation built on verified claims.",
          "", "## Summary", "", summary, ""]

    for name, heading in SECTIONS:
        r = results.get(name)
        md += [f"## {heading}", ""]
        if r is None or r.status != AgentStatus.success:
            reason = (r.error or "; ".join(r.limitations)) if r else "not run"
            md += [f"> **Unavailable.** {reason}", ""]
            continue
        mine = [c for c in verified if c.agent == name]
        for ctype in (ClaimType.FACT, ClaimType.CALCULATED, ClaimType.INTERPRETATION):
            md += [_line(c) for c in mine if c.type == ctype]
        if name == "news":
            md += ["", "| Date | Sentiment | Event | Headline |", "|---|---|---|---|"]
            for i in r.data.get("items", []):
                d = (i.get("published_at") or "")[:10] or "undated"
                md.append(f"| {d} | {i['sentiment']} | {i['event_type']} | [{i['title']}]({i['url']}) |")
        if name == "technical":
            md += ["", "Conditions: " + ("; ".join(r.data.get("conditions", [])) or "none")]
        md.append("")

    md += ["## Conflicting Findings", ""]
    md += [f"- **{c.severity.upper()}**: {c.description}" for c in contradictions] or ["No contradictions detected."]
    md += ["", "## Data Limitations and Uncertainty", ""]
    md += [f"- {l}" for l in limitations] or ["None recorded."]
    md += ["", "## Sources", "", "| Type | Title | Published | Retrieved | Hash |", "|---|---|---|---|---|"]
    for s in sources:
        title_s = f"[{s.title}]({s.source_url})" if s.source_url else s.title
        pub = s.published_at.strftime("%Y-%m-%d") if s.published_at else "-"
        md.append(f"| {s.source_type} | {title_s} | {pub} | {s.retrieved_at:%Y-%m-%d %H:%M} | `{s.content_hash[:10]}` |")
    md += ["", "---", "_This report is generated from public data for research purposes. It is not investment advice. "
           "Technical indicators describe historical conditions and are not predictions._", ""]
    return {"content": "\n".join(md), "summary": summary, "limitations": "\n".join(limitations), "score": score}
