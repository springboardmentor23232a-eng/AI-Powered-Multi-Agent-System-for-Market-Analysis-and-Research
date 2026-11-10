<USER_REQUEST>
# Veritas Equity Research Platform: Master Prompt (single source of truth)

This ONE prompt replaces `AGENT_MASTER_PROMPT.md` and `VERITAS_COMPLETION_BUILD_PROMPT.md`. If any older prompt or
earlier chat message conflicts with this, this wins. The only thing that outranks it is the project specification,
`docs/PROJECT_SPECIFICATION.pdf` ("Multi-Agent Stock Research Analyst"). If that PDF is missing, say so and ask me to add it.

**Operating mode.** You are the only agent working on this repository. Work autonomously through the phases in order.
Stop only at the listed stop-points or when blocked, and then ask one specific question. Do not ask for permission for
anything approved in section 7.

---

## 1. Mission, user, problem
- **User:** an analyst or student who needs a stock research report they can audit, not a confident narrative they must trust.
- **Problem:** LLM-written finance reports mix facts, calculations and opinion with no evidence trail.
- **Product:** a multi-agent research app for NSE equities (fixed 20-ticker universe) built with FastAPI, LangGraph,
  React and TypeScript, PostgreSQL. Every report line is a typed claim: `FACT`, `CALCULATED` or `INTERPRETATION`
  (shown as `FACT` / `CALC` / `AI`). Cross-agent disagreement is shown in a contradiction matrix. Research can be replayed as
  of a past date. Do not add new differentiators; finish and harden what exists. Keep complexity low.

**How the system actually works (use this wording in all docs; do not embellish):**
`POST /research` creates a task and runs it in the background. The LangGraph workflow validates the ticker and warms the
data cache (`plan`), runs the Fundamental, Technical and News agents in parallel with bounded retries on `ProviderError`,
then the Risk agent (which also runs the rule-based contradiction detector), then the Verifier, then the report builder.
The task executor persists results, claims, contradictions and the report to the database.
- The Risk agent computes annualised volatility and maximum drawdown. **There is no VaR.**
- The Verifier **checks**, it does not "prove": a FACT quote must appear in a stored source text whose content hash matches;
  a CALCULATED claim must reproduce when its tool is re-run; an INTERPRETATION may rest only on verified claims.
- The contradiction detector is a function the Risk agent calls, not a graph node.
- Rate limiting is an in-process sliding window; quotas are database-backed (3 active tasks, 30 per day per user).
- **Language guard:** never write "proves", "guarantees", "cryptographic", "hallucination-free" or "fully verified".
  Never report an automated 100% metric without the audit findings in section 4.

## 2. Standing rules (non-negotiable)
1. The LLM never does arithmetic or retrieval. All numbers come from `app/tools`. LLM text containing a number that was
   not in its facts is rejected (`numbers_grounded`) and replaced by the deterministic template text.
2. Only verified claims appear in a report. FACT quotes are literal substrings of stored `source_documents.content_excerpt`.
3. Never invent to fill a gap. Missing or failed data becomes `unavailable` plus a limitation. Only `ProviderError` is retried.
4. Replay is honest: news is skipped, financials are not point-in-time, only the technical signal is calibrated.
5. Tests never use the network. Use `tests/fakes.py`, `evaluation/synthetic.py` or small recorded fixtures (short titles only).
6. One API worker. No secrets in the repo or in chat. No buy/sell advice; the not-investment-advice line stays.
7. **Human-only judgments.** You never label the citation audit and never reinterpret my labels. Labels produced with
   Gemini are always described as "LLM-assisted (Gemini) with human spot-check", never as a manual audit.
8. Evidence first: inspect real data and the baseline results before changing behaviour. Label everything unverified.
9. Preserve behaviour, tests and audit trail. Never weaken or delete a test to make it pass. Never tune code to move a
   metric: fix real bugs and say so, and report regressions plainly.
10. Professional names for files, folders, branches, functions, commits and docs. No zip files unless I ask. Report findings
    and diffs as text.
11. One branch per change (`fix/...`, `feat/...`), small Conventional Commits, CI green before merge, no force-push, no
    deleting files without my approval.
12. Never replace the working tree from `veritas_repo_bundle.py` or any older zip. They predate the audit work and would
    destroy my labels.

## 3. Phase 0: setup and read-only verification (do first, then continue)
1. Confirm the working tree is the one containing `backend/`, `frontend/`, `docs/`, `audit_worksheet.html` and the
   `backend/eval_output/` audit files. Make a safety backup zip of it OUTSIDE the repo, excluding `.env`, `node_modules`,
   caches, `.git` and `*.db`.
2. If there is no git repository: `git init`, ensure `.env` is ignored, and commit the tree exactly as received
   ("chore: baseline snapshot as received"). This is setup, not a code change. Note that `eval_output/` is gitignored; use
   `git add -f` only for the copies under `docs/evaluation_results/` later.
3. Run `cd backend && pip install -r requirements.txt -r requirements-dev.txt && pytest -q` and
   `cd frontend && npm ci && npm test && npm run build`. Expected: backend about 90 passed and 2 skipped (those need
   `TEST_DATABASE_URL`), frontend 9 passed, build succeeds. Report any difference.
4. Check that `docs/PROJECT_SPECIFICATION.pdf` exists; if not, ask me.
5. Report in one short message, then proceed to Phase A. Make no code changes in this phase.

## 4. Current state (verified earlier, treat as the starting point)
**Built and tested:** auth (JWT, Argon2), market data service with validation and DB snapshot cache, indicator and ratio
library validated against TA-Lib and independent references, four agents, LangGraph supervisor, verifier, Markdown report,
research / claims / contradictions / watchlist / preferences APIs, React dashboard, evaluation harness (reference
calculations, failure drills, replay calibration), production hardening, production Compose with Caddy. Verified on
PostgreSQL 16 (migrations match models; concurrent workflows pass).

**Live verification done:** yfinance prices and financials, Google News RSS, and a full TCS task with every claim verified.
13 of 20 tickers have complete financial fields. Banks and NBFCs (HDFCBANK, ICICIBANK, SBIN, KOTAKBANK, AXISBANK,
BAJFINANCE) have no `operating_income` on Yahoo, which is a real limitation, not a label bug. NESTLEIND's newest fiscal
column is mostly empty.

**Baseline 20-ticker live evaluation exists** in `backend/eval_output/` (calculation agreement 325/325, 167/167 FACT
claims with a stored source, 620/620 claims verified, 5/5 failure drills). These are automated self-consistency checks.
They do not show the sources are right.

**Citation audit in progress (human labelling).** Preliminary findings, to be confirmed by the final labelled file:
- All 5 audited stored "closes" were intraday values fetched at or before 13:50 IST on 2026-11-05 and differ from the
  settled close by -0.44% to +0.13% (ULTRACEMCO 12,277.00 vs 12,250.00; INFY 1,165.90 vs 1,167.40; ASIANPAINT 2,534.90 vs
  2,523.80; AXISBANK 1,280.70 vs 1,280.00; ITC 279.40 vs 278.85; a Phase 1 capture of ITC was 279.35).
- About 7 of 30 audited news claims were quote or chart pages, not articles, stamped with a feed date.
- Price and financial source documents (10 audited rows) have an empty `source_url`.
- Price and financial facts come from Yahoo and were checked against Yahoo, so that part of the audit shows faithful storage,
  not independent truth. Multi-stock roundup headlines are accurate citations but weak evidence about one company.
- Gemini labelled all 5 price rows `yes`; the evidence says it did not read the source. Treat its labels with suspicion.

**Still unverified:** the live Anthropic adapter, the dashboard in a real browser, `docker compose` and Caddy HTTPS,
official announcement sources, Yahoo and news feed behaviour over time (both unofficial), real cost per report.

## 5. Specification compliance matrix (verified against the code)
DONE = built and tested. GAP = missing. PARTIAL = incomplete. EVID = needs a real run.

| Spec requirement | Status | Action |
|---|---|---|
| M1 Auth, JWT, history, watchlist, preferences | DONE | none |
| M2 Search, OHLCV, profile and financials, validation, NSE | DONE | none |
| M2 Data sources and retrieval timestamps | PARTIAL | price/financial sources lack links: **Fix #3** |
| M3 Revenue, profitability, debt, ratios | DONE | none |
| M3 Historical financial comparison | PARTIAL | only latest vs previous year: **C8** |
| M3 Peer comparison "where comparable data is available" | GAP | limitation text only: **C3** |
| M3 Missing or inconsistent data | PARTIAL | newest column may be empty: **C7** |
| M4 SMA, RSI, MACD, volatility, charts, conditions | DONE | none |
| M4 EMA | GAP | exists in `app/tools`, never computed by the Technical agent: **C1** |
| M4 Historical price trend analysis | PARTIAL | no period returns: **C1** |
| M5 News retrieval, sentiment, links, dates, conflicts | DONE | quality defect: **Fix #1** |
| M5 Official company announcements | GAP | **C4** (feasibility first) |
| M6 Volatility, drawdown, contradictions, scenarios, limits | DONE | leverage flag misfires for banks: **C6** |
| M6 Sector-related risks | PARTIAL | no sector awareness: **C6** |
| M7 Supervisor | DONE | planner is deterministic by design: **C9 (ask first)** |
| M8 Report sections | PARTIAL | no "Company Overview" section: **C2** |
| M8 Source links and timestamps | PARTIAL | **Fix #3** |
| M8 Downloadable PDF or Markdown | DONE (Markdown) | optional PDF via print: **C5** |
| M9 Dashboard | DONE | verify in a real browser: Phase E |
| M10 Endpoint tests, calculation validation, retries, citation audit | DONE | audit in progress: Phase A |
| M10 Cost per report | EVID | needs a real-LLM run: Phase D |
| M10 Deploy, HTTPS, CORS, logging, access controls | PARTIAL | config done, not deployed: Phase F |
| Limitations and future work documented | GAP | Phase G |
| Postman for API testing | GAP | **C10** |

## 6. Phases (in order)

### Phase A: finish the citation audit gate (BLOCKED ON ME)
Until I say **"labels saved"** and give a file path: no promotion, no scoring, no code changes. If I ask a question, answer it.
Labelling rules I use: exact date and value match = `yes`; same date but value differs = `partial` with the delta in the
note; wrong date, no such bar, or not a close = `no`. A quote or chart page is `partial` unless it is a real article.
When I say "labels saved":
1. Take the newest `citation_audit_sample_human_labeled_<timestamp>.csv` and run this integrity gate. Report every
   result, and do not promote if any check fails:
   - 40 rows; row order identical to `citation_audit_sample.csv`; `gemini_label` identical by position. The join key is
     `(ticker, claim_id)`, never `claim_id` alone, which repeats.
   - Every price row has a note stating where its number came from: `(checked on Yahoo page)` or
     `(yfinance re-fetch 2026-11-06; not checked on Yahoo page)`.
   - Every row where my label differs from Gemini's, including the six I resolved from `unverified`, has a note.
   - Labels are not uniform.
2. If the gate passes: promote the file, score it with `python -m app.evaluation.audit`, honour every label verbatim.
3. Report per-category agreement (news, price, financials) with 95% intervals and exact coverage computed from the file
   ("N of 40 rows human-labelled, M Gemini-only"). Never present the blended percentage as fully human-verified, and note
   that the human-labelled rows were chosen on purpose, not at random.
4. Copy `evaluation_report.md`, `results.json` and the labelled CSV (no database files) to
   `docs/evaluation_results/<date>-baseline/`, `git add -f`, and commit. This baseline is the "before" for everything
   below and must never be overwritten.
5. State in the write-up: stored prices were fetched at or before 13:50 IST (intraday); price and financial rows had no source link.
**Stop-point:** report, then continue to Phase B.

### Phase B: evidence-backed fixes (approved)
Each fix: write the test first (recorded or synthetic fixture), keep every invariant, and compare before/after in Phase D.

**Fix #1: non-article pages counted as news.** Filter in `NewsAgent` after fetch using title patterns (for example
"Share Price Today", "Live NSE", "Stock Price and Chart", "Share Price - Live", "Market News" suffix, "Stock Price & Chart")
and the feed's publisher name. Google News links are redirects, so do not filter on the final URL. Add the limitation "N items
excluded as non-article pages". Label multi-stock roundups (for example "Stocks in news: A, B, C, D") with
`event_type="roundup"`, keep them listed, and exclude them from the sentiment signal. Fixtures: the real titles from the audit.

**Fix #2: unfinished price bar presented as "close".** Implement in the market-data layer, before any indicator,
volatility or drawdown is computed:
- Decide using the snapshot's **retrieval time**, not the current time. If the last bar's date equals the retrieval date
  (Asia/Kolkata) and the retrieval time is before 16:00 IST (close plus buffer), the last bar is unfinished: drop it and add
  the validation issue `unfinished_session_dropped`, shown as a limitation.
- A snapshot fetched before the close is expired once the close has passed.
- The report says "as of last completed session (YYYY-MM-DD)" and shows the retrieval time in IST.
- Tests (use `zoneinfo`, no sleeping): fetched 13:50 IST same day (dropped), fetched 17:00 IST (kept), weekend and
  holiday (kept), cached mid-session then read next day (refetched), replay unaffected.

**Fix #3: price and financial sources have no link.** Store Yahoo URLs in `SourceDocument.source_url` for price
(`https://finance.yahoo.com/quote/{SYMBOL}/history/`), financials (`.../financials/`) and profile (`.../quote/{SYMBOL}/`) via an
optional provider method so fakes keep working. Show link, as-of date and retrieval time (IST) in the report's Sources table
and the dashboard. Report `source_url` coverage in `evaluation/metrics.py`.
**Stop-point:** report with test output and diffs, then continue.

### Phase C: close the specification gaps (approved except C9)
Keep each item minimal. Add tests, add independent references in `evaluation/reference.py` for any new tool, and keep the claim ledger rules.
- **C1 EMA and returns.** `ema20` as a CALCULATED claim and chart series; returns over 1M, 3M, 6M and 1Y (21, 63, 126, 252
  sessions) via `total_return`; one extra condition ("close above/below EMA 20"). Show in the Charts tab and Technical panel.
- **C2 Company Overview.** FACT claims for name, sector, industry, market cap and currency from the profile (extend the
  financials excerpt with canonical profile lines so quotes verify). New report section after the summary; update
  `REQUIRED_SECTIONS` in `evaluation/metrics.py` and the completeness tests.
- **C3 Peer comparison (minimal).** Peers are other universe tickers with the same `sector`. Add a pure tool
  `peer_median(metric, peers)` that derives each peer's metric from raw inputs via the existing ratio tools and takes the
  median of non-null values (at least 2). CALCULATED claims for net margin, ROE and, for non-financial sectors,
  debt-to-equity versus the peer median. Log each peer's financials as source documents for the task. Fewer than 2 comparable
  peers means a limitation and no claim. Show "vs peer median" in the Fundamentals panel.
- **C4 Official announcements, feasibility first.** Spend bounded effort checking whether BSE or NSE corporate
  announcements are retrievable for 3 tickers within their terms of use, without bypassing blocks, with a clear User-Agent and
  a low request rate. Report the finding BEFORE implementing. If viable: an `AnnouncementsProvider` with the news shape, items
  labelled "official announcement", FACT claims, recorded-fixture tests, merged into the News section. If not: document the
  limitation honestly and stop.
- **C5 PDF export (optional, cheap).** Print stylesheet plus a "Print / Save as PDF" button on the report view. No server-side
  PDF dependency. Verify in Chrome's print preview and say so.
- **C6 Sector-aware fundamentals and risk.** First inspect the baseline results for the six banks and NBFCs. If confirmed that
  "Leverage is high" fires on them: for `sector == "Financial Services"`, exclude debt-to-equity and operating margin from
  signal scoring and risk flags and add the limitation "leverage and operating margin are not comparable for banks and NBFCs".
- **C7 Latest-year completeness.** Use the newest fiscal year that has revenue and net income, state the year used, and add a
  limitation when a newer incomplete year was skipped (observed for NESTLEIND).
- **C8 Multi-year comparison.** Revenue and net income CAGR via the `cagr` tool when at least 3 years exist, with the year
  range in the claim text. Show in the Fundamentals panel.
- **C9 LLM planner. ASK FIRST, do not build.** The spec mentions an LLM for planning; ours is deterministic by design. Write a
  short justification and a constrained design (structured output limited to the three analysis agents plus an optional focus
  note, deterministic fallback, behind a flag) for `docs/LIMITATIONS_AND_FUTURE_WORK.md`, then ask me whether to build it.
- **C10 Postman and API docs.** A script that exports OpenAPI to `docs/openapi.json` and a Postman collection generated from
  it. The API documentation endpoint stays disabled in production.
**Stop-point after each item:** short report, tests green.

### Phase D: re-evaluate and measure (needs my labelling again)
1. `python -m app.evaluation.run --provider yahoo --news google --out eval_output_postfix --pause 2` on all 20 tickers.
2. Write `docs/evaluation_results/<date>-post-fix/` with report, results and a before/after table against the baseline for:
   calculation agreement, citation coverage and correctness, completion rate, usable report rate, report completeness, latency
   p50 and p95, source-link coverage, non-article news items, and unfinished-bar occurrences.
3. Generate a fresh audit sample focused on changed behaviour (news after Fix #1; price and financial rows with links). I
   label it; wait for "labels saved"; apply the same integrity gate as Phase A.
4. **Cost per report:** if `LLM_API_KEY` is set in the environment, run 5 tickers into `eval_cost_output` with the real LLM,
   confirm the current model price on the official Anthropic pricing page, use the output-token rate as a conservative upper
   bound and label it so. If no key exists, write "LLM cost not measured". Never put a key in the repo.
**Stop-point.**

### Phase E: real-browser verification
Run the stack. Use Playwright if installable, otherwise give me a manual checklist. Cover: register and sign in, search, start
research, status polling, every tab, Charts (including the Content-Security-Policy under Caddy), Markdown download, print to
PDF, replay, watchlist, preferences, sign out, 401 handling. Fix real defects with tests where practical. Done when there are
no console errors.

### Phase F: deployment (needs my host and domain)
Prepare everything, then follow `docs/DEPLOYMENT.md` and complete its smoke test, including HTTPS issuance and the Charts
tab. Do not touch any infrastructure without my explicit go-ahead. Record results and any CSP adjustment.

### Phase G: documentation and traceability
- `docs/LIMITATIONS_AND_FUTURE_WORK.md` from real results: audit findings (non-article pages, intraday bars, missing source
  links, circular price and financial checks, roundup articles), single worker, unofficial data sources, unmeasured items, the
  planner decision, prioritised enhancements.
- `docs/SPEC_TRACEABILITY.md`: every bullet in the specification (modules 1 to 10, milestone criteria, overall metrics) mapped
  to code, tests and evidence, with status DONE / PARTIAL / NOT DONE and the reason.
- Update `README.md` and the repo tree below. Regenerate `veritas_repo_bundle.py` only if I ask.
**Stop-point:** final report.

## 7. Approvals
**Approved (build without asking):** Phase B (fixes #1 to #3), Phase C items C1 to C8 and C10, the git setup in Phase 0.
**Ask first:** C9, any new paid service or infrastructure (Redis, queue, cloud resources), changing the supported market,
deleting files, changing any rule in section 2, relaxing any gate in Phase A.

## 8. Definition of done
- Every row in section 5 is DONE or has a documented, honest limitation that I have accepted.
- Backend and frontend tests pass in CI; the PostgreSQL job passes; migrations match models.
- Baseline and post-fix evaluation results are committed with a before/after table, and human-audit coverage stated exactly.
- Deployed over HTTPS with the smoke test passed, or documented as pending my host.
- `docs/SPEC_TRACEABILITY.md` exists and every entry is backed by a test, a metric or a file.

## 9. Report format after every phase or item
1. What changed: files and a text diff summary. 2. Exact commands run and results. 3. Evidence: tests added, metrics before and
after. 4. What is still unverified. 5. The next step, or one specific question if blocked.

## 10. Repository structure (current)
```
veritas-equity-research/
├── VERITAS_MASTER_PROMPT.md            this file
├── README.md  docker-compose.yml  docker-compose.prod.yml  .env.example  .env.production.example
├── audit_worksheet.html                browser worksheet for the human citation audit
├── .github/workflows/ci.yml            backend, backend-postgres, frontend
├── deploy/Caddyfile                    HTTPS, security headers, /api proxy
├── docs/                               DEPLOYMENT.md, PROJECT_SPECIFICATION.pdf, evaluation_results/ (to be added)
├── backend/
│   ├── alembic/versions/               0001 schema, 0002 market_snapshots, 0003 task metrics and claim refs
│   ├── app/
│   │   ├── main.py  core/              config guards, security, logging, ratelimit, database
│   │   ├── models/  schemas/  data/    10 tables, claim and agent contracts, 20-ticker universe
│   │   ├── tools/                      pure functions: indicators, risk, fundamentals, registry (run_tool)
│   │   ├── agents/                     fundamental, technical, news, risk, contradictions, base (ClaimBuilder)
│   │   ├── graph/workflow.py           LangGraph: plan -> [fundamental|technical|news] -> risk -> verify -> report
│   │   ├── services/                   market_data, validation, news, llm, verifier, report, research, maintenance
│   │   ├── api/                        auth, stocks, research, workspace
│   │   └── evaluation/                 run, metrics, reference, drills, replay, synthetic, audit, merge_audit_labels
│   ├── tests/                          fakes.py, unit/, integration/ (postgres test needs TEST_DATABASE_URL)
│   └── eval_output/                    baseline run and audit files (gitignored)
├── frontend/src/                       api, auth, components, lib, pages (Vite, React, TypeScript, Tailwind, Plotly)
└── scripts/                            phase1 live verification helpers
```
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-11-10T17:20:31+05:30.
</ADDITIONAL_METADATA>