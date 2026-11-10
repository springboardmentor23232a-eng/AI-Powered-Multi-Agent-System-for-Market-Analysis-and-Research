from app.schemas.agents import AgentResult, AgentStatus, ContradictionOut

OPPOSITE = {"bullish": "bearish", "bearish": "bullish"}


def _signal(r: AgentResult | None) -> str | None:
    return r.data.get("signal") if r and r.status == AgentStatus.success else None


def detect_contradictions(upstream: dict[str, AgentResult]) -> list[ContradictionOut]:
    """Rule-based. The LLM may later explain these, but never decides them."""
    out: list[ContradictionOut] = []
    names = [n for n in ("fundamental", "technical", "news") if _signal(upstream.get(n))]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            sa, sb = _signal(upstream[a]), _signal(upstream[b])
            if OPPOSITE.get(sa) == sb:
                out.append(ContradictionOut(agent_a=a, agent_b=b, severity="high",
                                            description=f"{a.capitalize()} analysis is {sa} while {b} analysis is {sb}"))
    fund, tech, news = upstream.get("fundamental"), upstream.get("technical"), upstream.get("news")
    m = fund.data.get("metrics", {}) if fund and fund.status == AgentStatus.success else {}
    nm, nmp, g = m.get("net_margin"), m.get("net_margin_prev"), m.get("revenue_growth")
    if _signal(tech) == "bullish" and nm is not None and nmp is not None and nm < nmp:
        out.append(ContradictionOut(agent_a="technical", agent_b="fundamental", severity="medium",
                                    description="Price momentum is positive but net margin declined year over year"))
    if _signal(news) == "bullish" and g is not None and g < 0:
        out.append(ContradictionOut(agent_a="news", agent_b="fundamental", severity="medium",
                                    description="News flow is positive but revenue declined year over year"))
    return out
