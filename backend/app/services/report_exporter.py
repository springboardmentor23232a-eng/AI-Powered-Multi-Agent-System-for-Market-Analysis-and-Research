import html
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from fpdf import FPDF
from app.models.research import ResearchReport

DISCLAIMER_TEXT = (
    "DISCLAIMER: This automated equity research report is synthesized for analytical and informational "
    "purposes by the FinCrew Multi-Agent Platform. It does not constitute personalized investment, legal, "
    "or tax advice, nor an offer or solicitation to buy or sell securities. Past performance does not guarantee "
    "future returns. All investments involve substantial risk of loss. Always consult a certified financial advisor."
)


def _safe_str(val: Any, default: str = "Unavailable") -> str:
    """Helper to convert values to clean strings safely."""
    if val is None or val == "":
        return default
    return str(val).strip()


def _safe_num(val: Any, prefix: str = "", suffix: str = "", decimals: int = 2) -> str:
    """Helper to format numerical figures safely."""
    if val is None:
        return "Unavailable"
    try:
        f = float(val)
        return f"{prefix}{f:,.{decimals}f}{suffix}"
    except (ValueError, TypeError):
        return "Unavailable"


def _format_large_money(val: Any) -> str:
    """Formats large monetary figures into readable units like $105.66B USD."""
    if val is None:
        return "Unavailable"
    try:
        f = float(val)
        abs_f = abs(f)
        sign = "-" if f < 0 else ""
        if abs_f >= 1e12:
            return f"{sign}${abs_f / 1e12:.2f}T USD"
        elif abs_f >= 1e9:
            return f"{sign}${abs_f / 1e9:.2f}B USD"
        elif abs_f >= 1e6:
            return f"{sign}${abs_f / 1e6:.2f}M USD"
        elif abs_f >= 1e3:
            return f"{sign}${abs_f / 1e3:.2f}K USD"
        return f"{sign}${abs_f:,.2f} USD"
    except (ValueError, TypeError):
        return "Unavailable"


def _format_margin_pct(val: Any) -> str:
    """Formats margin ratios into percentage strings like 28.0%."""
    if val is None:
        return "Unavailable"
    try:
        f = float(val)
        return f"{f * 100:.1f}%"
    except (ValueError, TypeError):
        return "Unavailable"


def _format_ratio_pct(val: Any) -> str:
    """Formats ratio figures into percentage strings like 84.29%."""
    if val is None:
        return "Unavailable"
    try:
        f = float(val)
        return f"{f:.2f}%"
    except (ValueError, TypeError):
        return "Unavailable"


class ReportPDF(FPDF):
    """Custom FPDF subclass with branded FinCrew header and footer."""

    def __init__(self, ticker: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.ticker = ticker

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 116, 139)  # Slate
        self.cell(0, 8, f"FinCrew Multi-Agent Equity Research | {self.ticker}", border="B", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} - Strictly Confidential & Institutional Use Only", border="T", align="C")


class ReportExporter:
    """
    Exports synthesized multi-agent research reports into institutional-grade formats:
    1. Markdown (.md)
    2. Structured JSON (.json)
    3. Standalone Responsive HTML (.html)
    4. Binary PDF (.pdf)
    """

    @classmethod
    def export_json(cls, report: ResearchReport) -> Dict[str, Any]:
        """Returns structured JSON dictionary containing complete analytical metadata."""
        fundamental = report.fundamental_data or {}
        market_res = fundamental.get("market_research", {})
        technical = report.technical_data or {}
        sentiment = report.sentiment_data or {}
        risk = report.risk_data or {}

        created_iso = report.created_at.isoformat() if hasattr(report.created_at, "isoformat") else str(report.created_at)

        return {
            "metadata": {
                "report_id": report.id,
                "session_id": report.session_id,
                "ticker": report.ticker,
                "company_name": report.company_name,
                "generated_at": created_iso,
                "generator": "FinCrew Multi-Agent Research System",
                "version": "1.0",
            },
            "summary": {
                "recommendation": report.recommendation,
                "confidence_score": report.confidence_score,
                "current_price": report.current_price,
                "target_price": report.target_price,
                "implied_upside_percent": round(((report.target_price - report.current_price) / report.current_price) * 100, 1)
                if (report.target_price and report.current_price and report.current_price > 0) else None,
                "executive_summary": report.executive_summary,
            },
            "specialist_analyses": {
                "market_research": market_res,
                "fundamental_analysis": {k: v for k, v in fundamental.items() if k != "market_research"},
                "technical_analysis": technical,
                "sentiment_analysis": sentiment,
                "risk_analysis": risk,
            },
            "disclaimer": DISCLAIMER_TEXT,
        }

    @classmethod
    def export_markdown(cls, report: ResearchReport) -> str:
        """Formats the research report as a clean, institutional Markdown document."""
        data = cls.export_json(report)
        meta = data["metadata"]
        summ = data["summary"]
        spec = data["specialist_analyses"]

        curr_p = _safe_num(summ["current_price"], prefix="$")
        targ_p = _safe_num(summ["target_price"], prefix="$")
        upside = f"{summ['implied_upside_percent']:+.1f}%" if summ["implied_upside_percent"] is not None else "N/A"
        conf = f"{int(summ['confidence_score'] * 100)}%"

        md_lines = [
            f"# Institutional Equity Research: {report.company_name} ({report.ticker})",
            "",
            f"**Generated:** {meta['generated_at'][:10]} | **Research System:** FinCrew Multi-Agent Committee | **Status:** Final",
            "",
            "---",
            "",
            "## Investment Committee Executive Summary",
            "",
            "| Metric | Valuation / Signal |",
            "| :--- | :--- |",
            f"| **Ticker** | `{report.ticker}` |",
            f"| **Company Name** | {report.company_name} |",
            f"| **Consensus Recommendation** | **{report.recommendation}** |",
            f"| **Committee Confidence** | {conf} |",
            f"| **Current Trading Price** | {curr_p} |",
            f"| **12-Month Target Price** | {targ_p} |",
            f"| **Implied Price Change** | {upside} |",
            "",
            "### Narrative Thesis",
            "",
            report.executive_summary.replace("\n", "\n\n"),
            "",
            "---",
            "",
            "## 1. Market Positioning & Industry Dynamics",
            "",
            f"- **Sector:** {_safe_str(spec['market_research'].get('sector'))}",
            f"- **Industry:** {_safe_str(spec['market_research'].get('industry'))}",
            f"- **Market Cap Classification:** {_safe_str(spec['market_research'].get('market_cap_category'))}",
            "",
            "**Key Findings:**",
        ]

        for finding in spec["market_research"].get("key_findings", []):
            md_lines.append(f"- {finding}")

        md_lines.extend([
            "",
            "## 2. Fundamental Health & Valuation Assessment",
            "",
            f"- **Valuation Assessment:** {_safe_str(spec['fundamental_analysis'].get('valuation_status'))}",
            f"- **Profitability Grade:** {_safe_str(spec['fundamental_analysis'].get('profitability_grade'))}",
            f"- **Solvency Risk:** {_safe_str(spec['fundamental_analysis'].get('solvency_risk'))}",
            f"- **Free Cash Flow:** {_format_large_money(spec['fundamental_analysis'].get('supporting_data', {}).get('free_cash_flow'))}",
            f"- **Total Cash Reserves:** {_format_large_money(spec['fundamental_analysis'].get('supporting_data', {}).get('total_cash'))}",
            f"- **Total Debt:** {_format_large_money(spec['fundamental_analysis'].get('supporting_data', {}).get('total_debt'))}",
            f"- **Debt-to-Equity Ratio:** {_format_ratio_pct(spec['fundamental_analysis'].get('supporting_data', {}).get('debt_to_equity'))}",
            f"- **Net Profit Margin:** {_format_margin_pct(spec['fundamental_analysis'].get('supporting_data', {}).get('profit_margins'))}",
            f"- **Operating Margin:** {_format_margin_pct(spec['fundamental_analysis'].get('supporting_data', {}).get('operating_margins'))}",
            "",
            "**Key Findings:**",
        ])

        for finding in spec["fundamental_analysis"].get("key_findings", []):
            md_lines.append(f"- {finding}")

        md_lines.extend([
            "",
            "## 3. Technical Momentum & Key Levels",
            "",
            f"- **Trend Direction:** {_safe_str(spec['technical_analysis'].get('trend_direction'))}",
            f"- **Momentum State:** {_safe_str(spec['technical_analysis'].get('momentum_state'))}",
            f"- **Key Support Level:** {_safe_num(spec['technical_analysis'].get('key_support'), prefix='$')}",
            f"- **Key Resistance Level:** {_safe_num(spec['technical_analysis'].get('key_resistance'), prefix='$')}",
            "",
            "**Key Findings:**",
        ])

        for finding in spec["technical_analysis"].get("key_findings", []):
            md_lines.append(f"- {finding}")

        md_lines.extend([
            "",
            "## 4. Market Sentiment & Media Digest",
            "",
            f"- **Sentiment Stance:** {_safe_str(spec['sentiment_analysis'].get('sentiment_label'))}",
            f"- **Normalized Score:** {_safe_num(spec['sentiment_analysis'].get('sentiment_score'), decimals=2)} (-1.0 to +1.0)",
            f"- **News Sample Size:** {_safe_str(spec['sentiment_analysis'].get('news_sample_size'))} headlines",
            "",
            "**Key Findings:**",
        ])

        for finding in spec["sentiment_analysis"].get("key_findings", []):
            md_lines.append(f"- {finding}")

        md_lines.extend([
            "",
            "## 5. Downside Risk Analysis & Bear Case",
            "",
            f"- **Assessed Risk Level:** {_safe_str(spec['risk_analysis'].get('risk_level'))}",
            f"- **Risk Score:** {_safe_num(spec['risk_analysis'].get('risk_score'), suffix='/10', decimals=1)}",
            f"- **Bear Case Scenario:** {_safe_str(spec['risk_analysis'].get('bear_case_scenario'))}",
            "",
            "**Key Vulnerabilities:**",
        ])

        for finding in spec["risk_analysis"].get("key_findings", []):
            md_lines.append(f"- {finding}")

        md_lines.extend([
            "",
            "---",
            "",
            "### Regulatory & Investment Disclaimer",
            "",
            f"> {DISCLAIMER_TEXT}",
            "",
        ])

        return "\n".join(md_lines)

    @classmethod
    def export_html(cls, report: ResearchReport) -> str:
        """Renders a self-contained, sanitized HTML document with responsive styling."""
        data = cls.export_json(report)
        meta = data["metadata"]
        summ = data["summary"]
        spec = data["specialist_analyses"]

        # Color badges based on recommendation
        rec = str(report.recommendation).upper()
        if "BUY" in rec:
            badge_color = "#16a34a"  # Green
            badge_bg = "#dcfce7"
        elif "SELL" in rec:
            badge_color = "#dc2626"  # Red
            badge_bg = "#fee2e2"
        else:
            badge_color = "#ca8a04"  # Amber
            badge_bg = "#fef9c3"

        curr_p = _safe_num(summ["current_price"], prefix="$")
        targ_p = _safe_num(summ["target_price"], prefix="$")
        upside = f"{summ['implied_upside_percent']:+.1f}%" if summ["implied_upside_percent"] is not None else "N/A"
        conf = f"{int(summ['confidence_score'] * 100)}%"

        # Format paragraphs
        summary_paragraphs = "".join(
            f"<p>{html.escape(p)}</p>" for p in report.executive_summary.split("\n\n") if p.strip()
        )

        def render_findings(items: List[str]) -> str:
            if not items:
                return "<p class='text-muted'>No specific findings logged.</p>"
            return "<ul>" + "".join(f"<li>{html.escape(str(item))}</li>" for item in items) + "</ul>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Equity Research Memo - {html.escape(report.ticker)}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 24px; }}
        .container {{ max-width: 900px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }}
        .header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-start; }}
        .header h1 {{ margin: 0 0 8px 0; color: #0f172a; font-size: 28px; }}
        .subtitle {{ color: #64748b; font-size: 14px; margin: 0; }}
        .badge {{ display: inline-block; padding: 6px 14px; border-radius: 9999px; font-weight: 700; font-size: 14px; color: {badge_color}; background-color: {badge_bg}; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 32px; }}
        .metric-card {{ background: #f1f5f9; padding: 16px; border-radius: 8px; text-align: center; }}
        .metric-card .label {{ font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; margin-bottom: 4px; }}
        .metric-card .value {{ font-size: 20px; color: #0f172a; font-weight: 700; }}
        .section {{ margin-bottom: 32px; }}
        .section h2 {{ font-size: 20px; color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 16px; }}
        ul {{ padding-left: 20px; color: #334155; }}
        li {{ margin-bottom: 6px; }}
        .disclaimer {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; font-size: 12px; color: #7f1d1d; border-radius: 0 8px 8px 0; margin-top: 40px; }}
        .text-muted {{ color: #94a3b8; font-style: italic; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>{html.escape(report.company_name)} ({html.escape(report.ticker)})</h1>
                <p class="subtitle">FinCrew Multi-Agent Investment Committee Report | Date: {html.escape(meta['generated_at'][:10])}</p>
            </div>
            <div class="badge">{html.escape(report.recommendation)}</div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="label">Current Price</div>
                <div class="value">{curr_p}</div>
            </div>
            <div class="metric-card">
                <div class="label">12-Mo Target</div>
                <div class="value">{targ_p}</div>
            </div>
            <div class="metric-card">
                <div class="label">Implied Change</div>
                <div class="value">{upside}</div>
            </div>
            <div class="metric-card">
                <div class="label">Confidence Score</div>
                <div class="value">{conf}</div>
            </div>
        </div>

        <div class="section">
            <h2>Executive Committee Narrative</h2>
            {summary_paragraphs}
        </div>

        <div class="section">
            <h2>1. Market Profile & Industry Positioning</h2>
            <p><strong>Sector:</strong> {html.escape(_safe_str(spec['market_research'].get('sector')))} | <strong>Industry:</strong> {html.escape(_safe_str(spec['market_research'].get('industry')))} | <strong>Capitalization:</strong> {html.escape(_safe_str(spec['market_research'].get('market_cap_category')))}</p>
            {render_findings(spec['market_research'].get('key_findings', []))}
        </div>

        <div class="section">
            <h2>2. Fundamental Health & Valuation Multiples</h2>
            <p><strong>Valuation:</strong> {html.escape(_safe_str(spec['fundamental_analysis'].get('valuation_status')))} | <strong>Profitability:</strong> {html.escape(_safe_str(spec['fundamental_analysis'].get('profitability_grade')))} | <strong>Solvency:</strong> {html.escape(_safe_str(spec['fundamental_analysis'].get('solvency_risk')))}</p>
            <p><strong>Free Cash Flow:</strong> {html.escape(_format_large_money(spec['fundamental_analysis'].get('supporting_data', {}).get('free_cash_flow')))} | <strong>Total Cash:</strong> {html.escape(_format_large_money(spec['fundamental_analysis'].get('supporting_data', {}).get('total_cash')))} | <strong>Total Debt:</strong> {html.escape(_format_large_money(spec['fundamental_analysis'].get('supporting_data', {}).get('total_debt')))}</p>
            <p><strong>Debt-to-Equity:</strong> {html.escape(_format_ratio_pct(spec['fundamental_analysis'].get('supporting_data', {}).get('debt_to_equity')))} | <strong>Profit Margin:</strong> {html.escape(_format_margin_pct(spec['fundamental_analysis'].get('supporting_data', {}).get('profit_margins')))} | <strong>Operating Margin:</strong> {html.escape(_format_margin_pct(spec['fundamental_analysis'].get('supporting_data', {}).get('operating_margins')))}</p>
            {render_findings(spec['fundamental_analysis'].get('key_findings', []))}
        </div>

        <div class="section">
            <h2>3. Technical Momentum & Price Posture</h2>
            <p><strong>Trend:</strong> {html.escape(_safe_str(spec['technical_analysis'].get('trend_direction')))} | <strong>Momentum:</strong> {html.escape(_safe_str(spec['technical_analysis'].get('momentum_state')))} | <strong>Support:</strong> {_safe_num(spec['technical_analysis'].get('key_support'), prefix='$')} | <strong>Resistance:</strong> {_safe_num(spec['technical_analysis'].get('key_resistance'), prefix='$')}</p>
            {render_findings(spec['technical_analysis'].get('key_findings', []))}
        </div>

        <div class="section">
            <h2>4. Media & Sentiment Digest</h2>
            <p><strong>Tone:</strong> {html.escape(_safe_str(spec['sentiment_analysis'].get('sentiment_label')))} | <strong>Score:</strong> {_safe_num(spec['sentiment_analysis'].get('sentiment_score'), decimals=2)} | <strong>Headlines Analyzed:</strong> {_safe_str(spec['sentiment_analysis'].get('news_sample_size'))}</p>
            {render_findings(spec['sentiment_analysis'].get('key_findings', []))}
        </div>

        <div class="section">
            <h2>5. Downside Risk Analysis & Bear Case</h2>
            <p><strong>Risk Severity:</strong> {html.escape(_safe_str(spec['risk_analysis'].get('risk_level')))} | <strong>Score:</strong> {_safe_num(spec['risk_analysis'].get('risk_score'), suffix='/10', decimals=1)}</p>
            <p><strong>Bear Case:</strong> {html.escape(_safe_str(spec['risk_analysis'].get('bear_case_scenario')))}</p>
            {render_findings(spec['risk_analysis'].get('key_findings', []))}
        </div>

        <div class="disclaimer">
            <strong>Legal Notice:</strong> {html.escape(DISCLAIMER_TEXT)}
        </div>
    </div>
</body>
</html>"""

    @classmethod
    def export_pdf(cls, report: ResearchReport) -> bytes:
        """
        Generates a genuine, beautifully formatted PDF equity research memo using fpdf2.
        Returns binary PDF bytes conforming to standard PDF-1.7 specifications.
        """
        data = cls.export_json(report)
        meta = data["metadata"]
        summ = data["summary"]
        spec = data["specialist_analyses"]

        pdf = ReportPDF(ticker=report.ticker)
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Sanitize text for standard PDF encoding (Latin-1 safe)
        def clean_pdf_text(text: str) -> str:
            if not text:
                return ""
            # Replace unsupported Unicode dashes and smart quotes with standard ASCII
            text = text.replace("—", "--").replace("–", "-")
            text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
            text = text.replace("•", "*")
            return text.encode("latin-1", "replace").decode("latin-1")

        # Title Block
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 10, clean_pdf_text(f"{report.company_name} ({report.ticker})"), new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, clean_pdf_text(f"FinCrew Multi-Agent Investment Committee Report | Date: {meta['generated_at'][:10]}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Recommendation & Key Metrics Banner
        rec_str = str(report.recommendation).upper()
        if "BUY" in rec_str:
            pdf.set_fill_color(220, 252, 231)  # Light Green
            pdf.set_text_color(22, 101, 52)     # Dark Green
        elif "SELL" in rec_str:
            pdf.set_fill_color(254, 226, 226)  # Light Red
            pdf.set_text_color(153, 27, 27)     # Dark Red
        else:
            pdf.set_fill_color(254, 249, 195)  # Light Yellow
            pdf.set_text_color(133, 77, 14)     # Dark Amber

        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, clean_pdf_text(f"  CONSENSUS RATING: {rec_str}  (Confidence: {int(report.confidence_score * 100)}%)"), fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        # Price Table
        curr_p = _safe_num(summ["current_price"], prefix="$")
        targ_p = _safe_num(summ["target_price"], prefix="$")
        upside = f"{summ['implied_upside_percent']:+.1f}%" if summ["implied_upside_percent"] is not None else "N/A"

        pdf.set_fill_color(241, 245, 249)
        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Helvetica", "B", 9)

        col_w = 47.5
        pdf.cell(col_w, 7, "Current Price", border=1, fill=True, align="C")
        pdf.cell(col_w, 7, "12-Mo Target", border=1, fill=True, align="C")
        pdf.cell(col_w, 7, "Implied Change", border=1, fill=True, align="C")
        pdf.cell(col_w, 7, "Confidence Score", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 10)
        pdf.cell(col_w, 8, clean_pdf_text(curr_p), border=1, align="C")
        pdf.cell(col_w, 8, clean_pdf_text(targ_p), border=1, align="C")
        pdf.cell(col_w, 8, clean_pdf_text(upside), border=1, align="C")
        pdf.cell(col_w, 8, clean_pdf_text(f"{int(report.confidence_score * 100)}%"), border=1, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # Executive Summary Section
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(pdf.epw, 7, "Executive Committee Narrative", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(51, 65, 85)
        pdf.multi_cell(pdf.epw, 5, clean_pdf_text(report.executive_summary), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Specialist Sections
        sections = [
            ("1. Market Profile & Industry Positioning", spec["market_research"]),
            ("2. Fundamental Health & Valuation Multiples", spec["fundamental_analysis"]),
            ("3. Technical Momentum & Key Price Levels", spec["technical_analysis"]),
            ("4. Market Sentiment & Media Digest", spec["sentiment_analysis"]),
            ("5. Downside Risk Analysis & Bear Case", spec["risk_analysis"]),
        ]

        for title, sec_data in sections:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(pdf.epw, 6, clean_pdf_text(title), new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(51, 65, 85)

            # Bullet points
            findings = sec_data.get("key_findings", [])
            if title.startswith("2. Fundamental"):
                f_sup = sec_data.get("supporting_data") or {}
                fcf_txt = _format_large_money(f_sup.get("free_cash_flow"))
                c_txt = _format_large_money(f_sup.get("total_cash"))
                d_txt = _format_large_money(f_sup.get("total_debt"))
                de_txt = _format_ratio_pct(f_sup.get("debt_to_equity"))
                pm_txt = _format_margin_pct(f_sup.get("profit_margins"))
                pdf.set_font("Helvetica", "I", 8.5)
                pdf.set_text_color(71, 85, 105)
                pdf.cell(pdf.epw, 5, clean_pdf_text(f"Metrics: FCF: {fcf_txt} | Cash: {c_txt} | Debt: {d_txt} | D/E: {de_txt} | Margin: {pm_txt}"), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(51, 65, 85)

            if findings:
                for f in findings:
                    pdf.multi_cell(pdf.epw, 5, clean_pdf_text(f"- {f}"), new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(pdf.epw, 5, "No specific findings logged.", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

        # Disclaimer Box
        pdf.ln(3)
        pdf.set_fill_color(254, 242, 242)
        pdf.set_text_color(127, 29, 29)
        pdf.set_font("Helvetica", "I", 7.5)
        pdf.multi_cell(pdf.epw, 4.5, clean_pdf_text(DISCLAIMER_TEXT), fill=True, border=1, new_x="LMARGIN", new_y="NEXT")

        return bytes(pdf.output())
