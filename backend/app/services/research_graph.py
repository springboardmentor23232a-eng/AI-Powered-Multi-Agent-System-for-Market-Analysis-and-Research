from typing import Any, TypedDict
from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.services.market_data import fetch_stock_history


class ResearchState(TypedDict):
    ticker: str
    market: str
    analysis_period: str
    market_data: dict[str, Any]
    quant_summary: str
    analyst_report_md: str


def market_data_node(state: ResearchState) -> dict[str, Any]:
    data = fetch_stock_history(
        ticker=state["ticker"],
        market=state["market"],
        analysis_period=state["analysis_period"],
    )
    return {"market_data": data}


def quant_analysis_node(state: ResearchState) -> dict[str, Any]:
    m = state["market_data"]["metrics"]
    currency = state["market_data"]["currency"]
    trend_signal = (
        "Bullish (Price above SMA-20 and SMA-50)"
        if m["latest_price"] > m["latest_sma_20"] >= m["latest_sma_50"]
        else "Bearish / Consolidating"
    )
    rsi_note = (
        "Overbought (>70)"
        if m["latest_rsi_14"] > 70
        else "Oversold (<30)"
        if m["latest_rsi_14"] < 30
        else "Neutral (30-70)"
    )
    quant_summary = (
        f"Latest Price: {m['latest_price']} {currency} | "
        f"Period Return: {m['period_return_pct']}% | "
        f"Annualized Volatility: {m['annualized_volatility_pct']}% | "
        f"SMA-20: {m['latest_sma_20']} | SMA-50: {m['latest_sma_50']} ({trend_signal}) | "
        f"RSI-14: {m['latest_rsi_14']} ({rsi_note}) | "
        f"5-Day Linear Regression Target: {m['linear_trend_5d_target']} {currency} (R²={m['linear_trend_r2']})"
    )
    return {"quant_summary": quant_summary}


def gemini_analyst_node(state: ResearchState) -> dict[str, Any]:
    data = state["market_data"]
    company = data["company_name"]
    yf_symbol = data["yf_symbol"]
    quant_summary = state["quant_summary"]

    prompt = f"""You are a senior equity research analyst. Write a concise, structured research brief in Markdown for {company} ({yf_symbol}) on {state['market']} over the {state['analysis_period']} period.

Verified Quantitative Data:
- Sector / Industry: {data['sector']} / {data['industry']}
- Metrics: {quant_summary}

Include these sections:
1. Executive Summary
2. Technical & Quantitative Signals (reference the exact SMA, RSI, volatility, and regression numbers above)
3. Key Risks & Watchpoints"""

    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your-gemini-api-key-here":
        try:
            from google import genai

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
            if response and response.text:
                return {"analyst_report_md": response.text}
        except Exception:
            pass

    m = data["metrics"]
    report_md = (
        f"## {company} ({yf_symbol}) — {state['analysis_period']} Research Brief\n\n"
        f"**Sector:** {data['sector']} | **Industry:** {data['industry']}\n\n"
        f"### Quantitative Snapshot\n"
        f"- **Latest Price:** {m['latest_price']} {data['currency']}\n"
        f"- **Period Return:** {m['period_return_pct']}%\n"
        f"- **Annualized Volatility:** {m['annualized_volatility_pct']}%\n"
        f"- **SMA-20 / SMA-50:** {m['latest_sma_20']} / {m['latest_sma_50']}\n"
        f"- **RSI-14:** {m['latest_rsi_14']}\n"
        f"- **5-Day Linear Trend Target:** {m['linear_trend_5d_target']} {data['currency']} (R² = {m['linear_trend_r2']})"
    )
    return {"analyst_report_md": report_md}


def build_research_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("market_data_node", market_data_node)
    graph.add_node("quant_analysis_node", quant_analysis_node)
    graph.add_node("gemini_analyst_node", gemini_analyst_node)

    graph.add_edge(START, "market_data_node")
    graph.add_edge("market_data_node", "quant_analysis_node")
    graph.add_edge("quant_analysis_node", "gemini_analyst_node")
    graph.add_edge("gemini_analyst_node", END)
    return graph.compile()


research_workflow = build_research_graph()


def run_stock_research(ticker: str, market: str, analysis_period: str) -> dict[str, Any]:
    result = research_workflow.invoke(
        {
            "ticker": ticker,
            "market": market,
            "analysis_period": analysis_period,
            "market_data": {},
            "quant_summary": "",
            "analyst_report_md": "",
        }
    )
    return {
        "market_data": result["market_data"],
        "quant_summary": result["quant_summary"],
        "analyst_report_md": result["analyst_report_md"],
    }