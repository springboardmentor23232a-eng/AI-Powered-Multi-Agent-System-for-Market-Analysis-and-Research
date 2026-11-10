# Baseline Evaluation & Citation Audit Report (Phase A)

**Date:** 2026-11-10  
**Baseline Directory:** `docs/evaluation_results/20261110-baseline/`  
**Source Labeled CSV:** `citation_audit_sample_human_labeled_20261110_2147.csv`  

---

## 1. Audit Overview & Methodology

This baseline citation audit evaluates 40 claims sampled across the 20-ticker live evaluation run (`eval_output/evaluation.db`).

### Provenance & Coverage Distinction:
- **24 Human-Labeled Rows (60.0%):** Evaluated and labeled directly by a human analyst with full inspection of source documents. These rows were **purposefully selected** rather than randomly sampled in order to inspect high-risk citation categories:
  - All 5 price claims (to compare stored intraday prices against official settled closes).
  - 17 news claims (including multi-stock roundups, headline-only pages, and third-party syndications).
  - 2 financial claims (balance sheet equity and income statement metrics).
- **16 Gemini-Only Rows with Human Spot-Checks (40.0%):** Initial labels produced via LLM assistance (Gemini) and verified via human spot-check:
  - 13 news claims (real corporate news items).
  - 3 financial claims (reported revenues and net income numbers).
- **Statistical Note on Confidence Intervals:** Because the sample was purposefully selected to scrutinize edge cases rather than drawn via simple random sampling, the reported Wilson score 95% confidence intervals are **illustrative only** and indicate sample precision rather than population parameters.

---

## 2. Key Baseline Audit Findings

1. **Intraday Price Bar Storage (5 of 5 Price Rows Partial):**
   - All 5 audited price rows (`ULTRACEMCO fundamental-9`, `INFY technical-1`, `ASIANPAINT technical-1`, `AXISBANK technical-1`, `ITC technical-1`) were fetched at or before 13:50 IST on 2026-11-05.
   - Because they were retrieved prior to the 15:30 IST market close and 16:00 IST settlement window, they represented intraday prices rather than settled official closes, differing by -0.44% to +0.13% from the settled close.
   - Human label assigned: `partial`. (Gemini had erroneously labeled all 5 price rows as `yes` without reading the source). All 5 rows now contain live canonical Yahoo Finance quote URLs with `(checked on Yahoo page)`.

2. **Empty Source Document URLs:**
   - Price and financial `source_documents` had an empty `source_url` field at the time of the baseline run, leaving no clickable audit trail in the frontend.

3. **Non-Article News Pages (6 of 30 News Rows Partial):**
   - 6 of the 30 audited news claims were stock quote/ticker landing pages or daily market wrap snippets (e.g., *"Share Price Today (NSE), Market News"*, *"stock price, news, quote and history"*), stamped with RSS feed dates rather than substantive investigative reporting.
   - Human label assigned: `partial`.

4. **Resolution of 6 Gemini Unverified News Rows:**
   - 6 rows where Gemini returned `unverified` were resolved to `yes` with factual, source-backed notes confirming that the quote is an exact verbatim substring of the stored source excerpt (`SBIN news-2`, `KOTAKBANK news-1`, `TCS news-3`, `SUNPHARMA news-5`, `ASIANPAINT news-3`, `ASIANPAINT news-2`).

---

## 3. Metric Breakdown

```json
{
  "labelled": 40,
  "yes": 29,
  "partial": 11,
  "no": 0,
  "strict_correctness_percent": 72.5,
  "lenient_correctness_percent": 100.0
}
```

### Per-Category Breakdown:

| Category | Total Rows | Human-Labeled | Gemini-Only (Spot-Checked) | Yes | Partial | No | Strict Correctness (Illustrative 95% CI) | Lenient Correctness (Illustrative 95% CI) |
|---|---|---|---|---|---|---|---|---|
| **Financials** | 5 | 2 | 3 | 5 | 0 | 0 | **100.0%** [56.6%, 100.0%] | **100.0%** [56.6%, 100.0%] |
| **News** | 30 | 17 | 13 | 24 | 6 | 0 | **80.0%** [62.7%, 90.5%] | **100.0%** [88.6%, 100.0%] |
| **Price** | 5 | 5 | 0 | 0 | 5 | 0 | **0.0%** [0.0%, 43.4%] | **100.0%** [56.6%, 100.0%] |
| **Overall** | 40 | 24 | 16 | 29 | 11 | 0 | **72.5%** [57.2%, 83.9%] | **100.0%** [91.2%, 100.0%] |

**Human vs. Gemini Agreement:** On the 18 evaluable human-checked rows (excluding the 6 where Gemini answered `unverified`), agreement was 13 / 18 (72.2%).

---

## 4. Status

This baseline snapshot is **FROZEN**. It represents the pre-fix state of the platform and serves as the benchmark against which Phase B fixes will be measured.
