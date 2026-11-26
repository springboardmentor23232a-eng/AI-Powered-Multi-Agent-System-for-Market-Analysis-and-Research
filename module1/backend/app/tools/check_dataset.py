"""Check the Kaggle reference dataset:   python -m app.tools.check_dataset [path/to/file.csv]

Prints which columns were recognised, which were ignored, how many companies/rows loaded, and whether the companies in the
built-in ticker list were found. Run this first when you add the CSV."""
import sys
from pathlib import Path

from ..catalog import CATALOG
from ..financial_dataset import DATASET_URL, DEFAULT_PATH, ALIASES, match_company, parse_csv


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT_PATH
    if not path.exists():
        print(f"No dataset file at {path}\n\n1. Download the CSV from {DATASET_URL}\n2. Save it as {DEFAULT_PATH}\n"
              f"   (or pass the path:  python -m app.tools.check_dataset C:\\path\\file.csv)")
        return 1
    try:
        ds = parse_csv(path)
    except ValueError as exc:
        print(f"PROBLEM: {exc}")
        return 2
    print(f"Loaded {path.name}: {len(ds.rows)} usable rows, {len(ds.companies())} companies")
    print("\nRecognised columns (canonical <- your header):")
    for canon, header in ds.column_map.items():
        print(f"  {canon:<26} <- {header}")
    missing = [c for c in ALIASES if c not in ds.column_map]
    print("\nNot found in this file (those metrics will show as 'not available'):", ", ".join(missing) or "none")
    print("Ignored columns:", ", ".join(ds.unmapped_columns) or "none")
    print("\nLoad report:", ds.report)
    hits = {s.ticker: match_company(ds, s.ticker, s.name) for s in CATALOG if s.market in ("NASDAQ", "NYSE")}
    found = {k: v for k, v in hits.items() if v}
    print(f"\nBuilt-in US tickers found in the dataset: {len(found)}/{len(hits)}")
    for t, c in list(found.items())[:15]:
        print(f"  {t:<6} -> {c}")
    print("\nSample company names in the file:", ", ".join(ds.companies()[:12]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
