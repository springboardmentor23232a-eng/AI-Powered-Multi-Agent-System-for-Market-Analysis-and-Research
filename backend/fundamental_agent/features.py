"""Turns financial figures into the ratios the model uses, and creates the health label."""
import numpy as np
import pandas as pd

from . import config as C

REQUIRED_RAW = [
    "revenue", "prev_revenue", "gross_profit", "net_income", "ebitda",
    "operating_cash_flow", "current_assets", "current_liabilities",
    "total_debt", "equity", "total_assets",
]

RAW_LABELS = {
    "revenue": "Revenue",
    "prev_revenue": "Previous-year revenue",
    "gross_profit": "Gross profit",
    "net_income": "Net income",
    "ebitda": "EBITDA",
    "operating_cash_flow": "Operating cash flow",
    "current_assets": "Current assets",
    "current_liabilities": "Current liabilities",
    "total_debt": "Total debt",
    "equity": "Shareholders' equity",
    "total_assets": "Total assets",
}


def debt_equity_ratio(total_debt, equity):
    if equity <= 0:
        return C.DEBT_EQUITY_CAP
    return min(total_debt / equity, C.DEBT_EQUITY_CAP)


def features_from_raw(raw: dict) -> dict:
    """Used at run time: raw statement figures -> the 8 model features."""
    rev = float(raw["revenue"])
    return {
        "gross_margin": float(raw["gross_profit"]) / rev * 100,
        "net_margin": float(raw["net_income"]) / rev * 100,
        "ebitda_margin": float(raw["ebitda"]) / rev * 100,
        "ocf_margin": float(raw["operating_cash_flow"]) / rev * 100,
        "current_ratio": float(raw["current_assets"]) / float(raw["current_liabilities"]),
        "debt_equity": debt_equity_ratio(float(raw["total_debt"]), float(raw["equity"])),
        "roa": float(raw["net_income"]) / float(raw["total_assets"]) * 100,
        "rev_growth": (rev / float(raw["prev_revenue"]) - 1) * 100,
    }


def health_score(f) -> int:
    nm = f["net_margin"]
    score = 2 if nm >= C.STRONG_NET_MARGIN else (1 if nm >= 0 else 0)
    score += int(f["roa"] >= C.MIN_ROA)
    score += int(f["ocf_margin"] >= C.MIN_OCF_MARGIN)
    score += int(f["current_ratio"] >= C.MIN_CURRENT_RATIO)
    score += int(f["rev_growth"] > 0)
    return score


def label_from_score(score: int) -> str:
    if score >= C.STRONG_AT:
        return "Strong"
    if score >= C.MODERATE_AT:
        return "Moderate"
    return "Weak"


def training_table(df: pd.DataFrame) -> pd.DataFrame:
    """Used in training: cleaned Kaggle rows -> feature table with the rubric label."""
    df = df.sort_values(["Company", "Year"]).reset_index(drop=True)
    rev = df["Revenue"]
    t = pd.DataFrame({"Company": df["Company"], "Year": df["Year"], "Category": df["Category"]})
    t["gross_margin"] = df["Gross Profit"] / rev * 100
    t["net_margin"] = df["Net Income"] / rev * 100
    t["ebitda_margin"] = df["EBITDA"] / rev * 100
    t["ocf_margin"] = df["Cash Flow from Operating"] / rev * 100
    t["current_ratio"] = df["Current Ratio"]
    t["debt_equity"] = np.where(
        df["Share Holder Equity"] <= 0,
        C.DEBT_EQUITY_CAP,
        np.minimum(df["Debt/Equity Ratio"], C.DEBT_EQUITY_CAP),
    )
    t["roa"] = df["ROA"]
    t["rev_growth"] = df.groupby("Company")["Revenue"].pct_change() * 100
    t = t.dropna(subset=["rev_growth"]).reset_index(drop=True)  # first year of each company has no growth
    t["score"] = t.apply(health_score, axis=1)
    t["label"] = t["score"].map(label_from_score)
    return t
