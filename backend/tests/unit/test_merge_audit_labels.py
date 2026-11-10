"""Offline tests for the audit-label merge tool (no network, uses tmp_path)."""
import csv
from pathlib import Path

import pytest

from app.evaluation import merge_audit_labels as mal

HEADER = ["ticker", "claim_id", "agent", "claim_text", "quote", "source_type", "source_url", "source_excerpt", "supported"]


def _write_csv(path: Path, claim_ids):
    rows = [{"ticker": "X", "claim_id": c, "agent": "news", "claim_text": c, "quote": c,
             "source_type": "news", "source_url": "http://example", "source_excerpt": "e", "supported": ""}
            for c in claim_ids]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)


def test_merge_applies_labels_backs_up_and_leaves_unverified_blank(tmp_path):
    csvp = tmp_path / "audit.csv"
    _write_csv(csvp, ["news-2", "news-3", "news-1"])
    table = tmp_path / "t.md"
    table.write_text(
        "| Row | Claim ID | Label | Note |\n|---|---|---|---|\n"
        "| 2 | `news-2` | **yes** | ok |\n"
        "| 3 | `news-3` | **partial** | meh |\n"
        "| 4 | `news-1` | **unverified** | dead link |\n", encoding="utf-8")

    res = mal.merge(csvp, table)

    assert (tmp_path / "audit.orig.csv").exists()  # original preserved
    rows, fields = mal.read(csvp)
    assert [r["supported"] for r in rows] == ["yes", "partial", ""]  # unverified stays blank
    assert [r["gemini_label"] for r in rows] == ["yes", "partial", "unverified"]
    assert {"gemini_label", "human_checked"}.issubset(fields)
    assert res["labelled"] == 2 and res["blank"] == 1
    assert res["yes"] == 1 and res["partial"] == 1 and res["no"] == 0


def test_merge_refuses_on_claimid_mismatch_and_writes_nothing(tmp_path):
    csvp = tmp_path / "audit.csv"
    _write_csv(csvp, ["news-2", "news-3"])
    table = tmp_path / "t.md"
    table.write_text("| 2 | `news-2` | **yes** |\n| 3 | `WRONG-9` | **no** |\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        mal.merge(csvp, table)

    assert not (tmp_path / "audit.orig.csv").exists()
    rows, _ = mal.read(csvp)
    assert all(r["supported"] == "" for r in rows)  # unchanged


def test_summary_reports_human_llm_agreement_and_overrides(tmp_path):
    csvp = tmp_path / "audit.csv"
    _write_csv(csvp, ["news-2", "news-3"])
    table = tmp_path / "t.md"
    table.write_text("| 2 | `news-2` | **yes** |\n| 3 | `news-3` | **yes** |\n", encoding="utf-8")
    mal.merge(csvp, table)

    # Human verifies both: agrees with row 2, overrides row 3 to partial.
    rows, fields = mal.read(csvp)
    rows[0]["human_checked"] = "yes"
    rows[1]["human_checked"] = "yes"
    rows[1]["supported"] = "partial"
    mal.write(csvp, rows, fields)

    s = mal.summary(csvp)
    assert s["human_checked_rows"] == 2 and s["human_vs_llm_compared"] == 2
    assert s["agreement_percent"] == 50.0 and s["human_overrides"] == 1
