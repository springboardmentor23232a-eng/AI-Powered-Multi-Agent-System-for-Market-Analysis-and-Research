"""Reference dataset: "Financial Statements of Major Companies (2009-2023)" from Kaggle (rish59).
https://www.kaggle.com/datasets/rish59/financial-statements-of-major-companies2009-2023

The file is NOT bundled (Kaggle needs a login and the licence is the author's). Download the CSV, then either
  * put it at  backend/data/financial_statements.csv   (auto-detected), or
  * set FINANCIALS_DATASET_PATH=/path/to/file.csv in backend/.env
and check it with   python -m app.tools.check_dataset
Column names are matched loosely (case, spaces and punctuation ignored) because exports differ; unknown columns are ignored
and anything missing becomes "not available" - never a guessed value. Monetary units are whatever the CSV uses; every
ratio the agents calculate is unit-free.
"""
import csv
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from .config import settings

DATASET_NAME = "Kaggle: Financial Statements of Major Companies (2009-2023)"
DATASET_URL = "https://www.kaggle.com/datasets/rish59/financial-statements-of-major-companies2009-2023"
DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "financial_statements.csv"

ALIASES: dict[str, tuple[str, ...]] = {
    "company": ("company", "companyname", "name", "ticker", "symbol"),
    "category": ("category", "sector", "industry"),
    "year": ("year", "fiscalyear", "fy"),
    "market_cap": ("marketcapinbusd", "marketcap", "marketcapbusd", "marketcapitalization"),
    "revenue": ("revenue", "totalrevenue", "sales", "netsales"),
    "gross_profit": ("grossprofit",),
    "net_income": ("netincome", "netprofit"),
    "eps": ("earningpershare", "earningspershare", "eps", "epsbasic"),
    "ebitda": ("ebitda",),
    "equity": ("shareholderequity", "shareholdersequity", "totalequity", "stockholdersequity", "totalshareholderequity"),
    "operating_cash_flow": ("cashflowfromoperating", "cashflowfromoperatingactivities", "operatingcashflow", "cashflowfromoperations"),
    "investing_cash_flow": ("cashflowfrominvesting", "cashflowfrominvestingactivities"),
    "financing_cash_flow": ("cashflowfromfinancialactivities", "cashflowfromfinancingactivities", "cashflowfromfinancing"),
    "reported_current_ratio": ("currentratio",),
    "reported_debt_to_equity": ("debtequityratio", "debttoequity", "debtequity", "debttoequityratio"),
    "reported_roe": ("roe", "returnonequity"),
    "reported_roa": ("roa", "returnonassets"),
    "reported_roi": ("roi", "returnoninvestment"),
    "reported_net_margin": ("netprofitmargin", "netmargin"),
    "free_cash_flow_per_share": ("freecashflowpershare", "fcfpershare"),
    "employees": ("numberofemployees", "employees"),
}
NUMERIC = [k for k in ALIASES if k not in ("company", "category")]


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _num(v):
    if v is None:
        return None
    t = str(v).strip().replace(",", "").replace("$", "").replace("%", "")
    if t == "" or t.lower() in {"n/a", "na", "nan", "none", "null", "-", "--"}:
        return None
    try:
        return float(t)
    except ValueError:
        return None


@dataclass
class Dataset:
    path: str
    loaded_at: datetime
    rows: list[dict]
    column_map: dict[str, str]                      # canonical -> original header
    unmapped_columns: list[str]
    report: dict = field(default_factory=dict)

    def companies(self) -> list[str]:
        return sorted({r["company"] for r in self.rows})


def parse_csv(path: Path) -> Dataset:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        by_norm = {_norm(h): h for h in headers}
        colmap = {canon: by_norm[a] for canon, aliases in ALIASES.items() for a in aliases if a in by_norm}
        # first alias wins per canonical name
        colmap = {c: next(by_norm[a] for a in ALIASES[c] if a in by_norm) for c in colmap}
        missing_required = [c for c in ("company", "year") if c not in colmap]
        if missing_required or not ({"revenue", "net_income"} & set(colmap)):
            raise ValueError(f"{path.name}: cannot find the columns {missing_required or ['revenue / net income']}. "
                             f"Columns found: {headers}")
        rows, problems = [], {"rows_read": 0, "rows_skipped_no_company_or_year": 0, "duplicate_company_year": 0,
                              "cells_missing": 0}
        seen = set()
        for raw in reader:
            problems["rows_read"] += 1
            company = (raw.get(colmap["company"]) or "").strip()
            year = _num(raw.get(colmap["year"]))
            if not company or year is None:
                problems["rows_skipped_no_company_or_year"] += 1
                continue
            rec = {"company": company, "year": int(year),
                   "category": (raw.get(colmap["category"]) or "").strip() if "category" in colmap else ""}
            for k in NUMERIC:
                if k == "year":
                    continue
                v = _num(raw.get(colmap[k])) if k in colmap else None
                rec[k] = v
                problems["cells_missing"] += v is None and k in colmap
            key = (company.lower(), rec["year"])
            if key in seen:
                problems["duplicate_company_year"] += 1
                rows = [r for r in rows if (r["company"].lower(), r["year"]) != key]  # keep the last occurrence
            seen.add(key)
            rows.append(rec)
    if not rows:
        raise ValueError(f"{path.name}: no usable rows.")
    mapped_headers = set(colmap.values())
    return Dataset(str(path), datetime.now(timezone.utc), rows, colmap,
                   [h for h in headers if h not in mapped_headers], {**problems, "rows_used": len(rows),
                                                                    "companies": len({r["company"] for r in rows})})


def _path() -> Path | None:
    if settings.financials_dataset_path:
        return Path(settings.financials_dataset_path).expanduser()
    return DEFAULT_PATH if DEFAULT_PATH.exists() else None


@lru_cache(maxsize=1)
def _load(path: str | None):
    if not path or not Path(path).exists():
        return None
    return parse_csv(Path(path))


def get_dataset() -> Dataset | None:
    """None when no dataset file is configured / present. Raises ValueError if a configured file is unreadable."""
    return _load(str(_path()) if _path() else None)


def clear_cache() -> None:
    _load.cache_clear()


def _match_key(s: str) -> str:
    s = re.sub(r"\b(inc|corp|corporation|co|ltd|limited|plc|company|holdings|class a|the)\b\.?", " ", s.lower())
    return _norm(s)


def match_company(ds: Dataset, ticker: str, name: str) -> str | None:
    """Find the dataset's spelling of this company by ticker or name (exact first, then containment)."""
    names = {r["company"] for r in ds.rows}
    tk, nm = _norm(ticker), _match_key(name)
    for c in names:
        if _norm(c) in (tk, _norm(name)) or _match_key(c) == nm:
            return c
    for c in names:
        k = _match_key(c)
        if len(k) >= 4 and (k in nm or nm in k):
            return c
    return None


def series_for(ds: Dataset, company: str) -> dict:
    """Per-year records for one company, oldest -> newest, in the shape the Fundamental agent uses."""
    recs = sorted((r for r in ds.rows if r["company"] == company), key=lambda r: r["year"])
    get = lambda k: [r.get(k) for r in recs]
    return {
        "periods": [str(r["year"]) for r in recs], "category": next((r["category"] for r in recs if r["category"]), ""),
        "metrics": {
            "revenue": get("revenue"), "gross_profit": get("gross_profit"), "net_income": get("net_income"),
            "equity": get("equity"), "eps": get("eps"), "ebitda": get("ebitda"),
            "operating_cash_flow": get("operating_cash_flow"),
            "reported_current_ratio": get("reported_current_ratio"), "reported_debt_to_equity": get("reported_debt_to_equity"),
            "reported_roe": get("reported_roe"), "reported_roa": get("reported_roa"), "reported_net_margin": get("reported_net_margin"),
            "market_cap": get("market_cap"),
        },
    }


def peers(ds: Dataset, company: str, category: str, year: int) -> list[dict]:
    return [r for r in ds.rows if r["company"] != company and r["year"] == year and category and r["category"] == category]
