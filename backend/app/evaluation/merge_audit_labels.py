#!/usr/bin/env python3
"""Merge an LLM-produced audit table into citation_audit_sample.csv and summarise the human spot-check.

    python merge_audit_labels.py merge   citation_audit_sample.csv gemini_table.md
    python merge_audit_labels.py summary citation_audit_sample.csv

`merge` reads a Markdown table with columns: row number | claim_id | label | ... (row 2 = first data row of the CSV),
refuses to run if any claim_id does not match the CSV row, keeps the original file as <name>.orig.csv, and adds
`gemini_label` and `human_checked` columns. `unverified` rows stay blank in `supported`.

Human workflow: after verifying a row yourself, set `human_checked` to `yes` and, if you disagree, change `supported`.
`summary` reports label counts and the human/LLM agreement rate on the rows you checked.
"""
import csv
import json
import re
import shutil
import sys
from pathlib import Path

ROW = re.compile(r"^\|\s*\**(\d+)\**\s*\|\s*`?([\w.-]+)`?\s*\|\s*\**(yes|partial|no|unverified)\**\s*\|", re.I)
VALID = {"yes", "partial", "no"}


def read(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r), list(r.fieldnames or [])


def write(path: Path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def merge(csv_path: Path, table_path: Path) -> dict:
    rows, fields = read(csv_path)
    parsed = {}
    for line in table_path.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line.strip())
        if m:
            n = int(m.group(1))
            if n in parsed:
                sys.exit(f"Duplicate row number {n} in the table")
            parsed[n] = (m.group(2), m.group(3).lower())
    expected = set(range(2, len(rows) + 2))
    if set(parsed) != expected:
        sys.exit(f"Table rows do not match the CSV: missing {sorted(expected - set(parsed))}, extra {sorted(set(parsed) - expected)}")
    bad = [(n, parsed[n][0], rows[n - 2]["claim_id"]) for n in sorted(parsed) if parsed[n][0] != rows[n - 2]["claim_id"]]
    if bad:
        sys.exit("claim_id mismatch (table vs CSV), nothing written: " + "; ".join(f"row {n}: {a} != {b}" for n, a, b in bad))
    backup = csv_path.with_suffix(".orig.csv")
    if not backup.exists():
        shutil.copy(csv_path, backup)
    for extra in ("gemini_label", "human_checked"):
        if extra not in fields:
            fields.append(extra)
    for n, (_, label) in parsed.items():
        row = rows[n - 2]
        row["gemini_label"] = label
        row["supported"] = label if label in VALID else ""
        row.setdefault("human_checked", "")
        row["human_checked"] = row.get("human_checked") or ""
    write(csv_path, rows, fields)
    return summary(csv_path)


def summary(csv_path: Path) -> dict:
    rows, _ = read(csv_path)
    counts = {k: sum(r["supported"].strip().lower() == k for r in rows) for k in VALID}
    labelled = sum(counts.values())
    checked = [r for r in rows if r.get("human_checked", "").strip().lower() == "yes"]
    compared = [r for r in checked if r.get("gemini_label") in VALID]
    agree = sum(r["supported"].strip().lower() == r["gemini_label"] for r in compared)
    return {"rows": len(rows), "labelled": labelled, **counts, "blank": len(rows) - labelled,
            "strict_correctness_percent": round(100 * counts["yes"] / labelled, 1) if labelled else None,
            "human_checked_rows": len(checked), "human_vs_llm_compared": len(compared),
            "agreement_percent": round(100 * agree / len(compared), 1) if compared else None,
            "human_overrides": len(compared) - agree}


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "merge" and len(sys.argv) == 4:
        print(json.dumps(merge(Path(sys.argv[2]), Path(sys.argv[3])), indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == "summary":
        print(json.dumps(summary(Path(sys.argv[2])), indent=2))
    else:
        sys.exit(__doc__)
