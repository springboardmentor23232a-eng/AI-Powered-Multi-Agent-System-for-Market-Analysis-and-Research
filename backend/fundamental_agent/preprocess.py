"""Cleans the Kaggle dataset and records every check and fix (bullet 6)."""
import pandas as pd

from . import config as C


def clean(df_raw: pd.DataFrame):
    steps = []

    def log(check, found, action):
        steps.append({"check": check, "found": found, "action": action})

    df = df_raw.copy()

    # 1. column names with hidden spaces
    messy = [c for c in df.columns if c != c.strip()]
    df.columns = df.columns.str.strip()
    log("Column names",
        f"{len(messy)} name(s) with stray spaces: {messy}" if messy else "none",
        "Stripped the spaces" if messy else "-")

    # 2. text columns
    for col in ("Company", "Category"):
        df[col] = df[col].astype(str).str.strip()

    # 3. category spelling
    before = sorted(df["Category"].unique())
    df["Category"] = df["Category"].replace({"BANK": "Bank"})
    after = sorted(df["Category"].unique())
    log("Category spelling",
        f"{len(before)} labels, 'BANK' and 'Bank' are the same sector",
        f"Merged into 'Bank' ({len(after)} categories left)" if len(after) < len(before) else "-")

    # 4. missing values
    miss = df.isna().sum()
    miss = miss[miss > 0]
    if len(miss):
        where = []
        for col in miss.index:
            rows = df.loc[df[col].isna(), ["Company", "Year"]]
            where.append(f"{col}: " + ", ".join(f"{r.Company} {r.Year}" for r in rows.itertuples()))
        log("Missing values", "; ".join(where),
            "Kept as missing. This column is in USD and is not used by the model")
    else:
        log("Missing values", "none", "-")

    # 5. duplicate company-year rows
    dup = df.duplicated(["Company", "Year"], keep="first")
    log("Duplicate company-year rows", f"{int(dup.sum())}", "Dropped" if dup.any() else "-")
    df = df[~dup]

    # 6. gaps in the years of a company
    gaps = []
    for comp, d in df.groupby("Company"):
        years = set(d["Year"])
        missing_years = sorted(set(range(min(years), max(years) + 1)) - years)
        if missing_years:
            gaps.append(f"{comp}: {missing_years}")
    log("Missing years inside a company's history", "; ".join(gaps) if gaps else "none",
        "Growth is only computed between consecutive years" if gaps else "-")

    # 7. impossible values
    bad = (
        (df["Revenue"] <= 0)
        | (df["Gross Profit"] > df["Revenue"])
        | ((df["Earning Per Share"] > 0) != (df["Net Income"] > 0))
        | (df["Market Cap(in B USD)"] <= 0)
    )
    log("Impossible values (revenue <= 0, gross profit > revenue, EPS sign differs from net income, market cap <= 0)",
        f"{int(bad.sum())} row(s)", "Dropped" if bad.any() else "-")
    df = df[~bad].copy()

    # 8. figures that do not agree with each other (kept, but flagged)
    calc_margin = df["Net Income"] / df["Revenue"] * 100
    df["flag_margin_mismatch"] = (calc_margin - df["Net Profit Margin"]).abs() > 1
    eq = df["Share Holder Equity"]
    calc_roe = df["Net Income"] / eq.where(eq != 0) * 100
    df["flag_roe_mismatch"] = (calc_roe - df["ROE"]).abs() > 5
    df["flag_negative_equity"] = eq < 0

    def names(mask):
        return ", ".join(f"{r.Company} {r.Year}" for r in df.loc[mask, ["Company", "Year"]].itertuples()) or "none"

    log("Stated net margin differs from Net Income / Revenue by more than 1 point",
        f"{int(df['flag_margin_mismatch'].sum())}: {names(df['flag_margin_mismatch'])}",
        "Kept and flagged. The model recomputes net margin itself")
    log("Stated ROE differs from Net Income / Equity by more than 5 points",
        f"{int(df['flag_roe_mismatch'].sum())}: {names(df['flag_roe_mismatch'])}",
        "Kept and flagged. ROE is not used as a model feature")
    log("Negative shareholder equity (ROE and debt-to-equity become misleading)",
        f"{int(df['flag_negative_equity'].sum())}: {names(df['flag_negative_equity'])}",
        f"Kept. Debt-to-equity is set to the cap of {C.DEBT_EQUITY_CAP:g} for these rows")

    # 9. extreme ratios
    ext = (df["ROE"].abs() > 100) | (df["ROI"].abs() > 100) | (df["Return on Tangible Equity"].abs() > 100)
    log("Extreme ROE / ROI / return on tangible equity (above 100 percent in size)",
        f"{int(ext.sum())} row(s)", "Kept. These three columns are not used as model features")

    return df.reset_index(drop=True), steps


def report_markdown(steps, rows_before: int, rows_after: int) -> str:
    lines = [
        "# Data cleaning report (Financial_Statements.csv)",
        "",
        f"Rows before cleaning: {rows_before}. Rows after cleaning: {rows_after}.",
        "",
        "| Check | What was found | Action taken |",
        "|---|---|---|",
    ]
    for s in steps:
        lines.append(f"| {s['check']} | {s['found']} | {s['action']} |")
    return "\n".join(lines) + "\n"


def load_and_clean():
    raw = pd.read_csv(C.RAW_CSV)
    df, steps = clean(raw)
    return raw, df, steps
