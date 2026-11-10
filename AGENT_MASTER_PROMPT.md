# Master Prompt: Veritas Equity Research Platform

You are the lead engineer continuing an existing, working codebase. Read this whole prompt, then follow the
phases in section 7. Do not rebuild anything that already works.

## 0. First: restore the repository (setup step, allowed before Phase 0)
The complete repository is delivered as ONE text file, `veritas_repo_bundle.py` (not a zip), because files downloaded
one by one lose their folders and same-named files (`risk.py`, `news.py`, `README.md`) overwrite each other.
- If `backend/app/main.py` does not exist in the working folder: put `veritas_repo_bundle.py` in an empty folder and run
  `python veritas_repo_bundle.py --dest .`. It must end with `all checksums verified`.
- Ignore any loose flat files or `files*.zip` archives from earlier downloads. Never reconstruct code from them.
- If `veritas_repo_bundle.py` is missing, stop and ask me for it. Do not rebuild the project from fragments.
- Restoring is setup, not a change to the project. After it, Phase 0 stays strictly read-only.

## 1. Mission and users
Build and finish **Veritas Equity Research Platform**: a multi-agent stock research web app for NSE-listed companies
(20-ticker universe). Real user: an analyst or student who wants a research report they can audit, not a confident
narrative they must trust. Real problem: LLM-written finance reports mix facts, calculations and opinion with no
evidence trail. Veritas makes every report line a typed, verified claim and shows where the agents disagree.

The project specification is in `docs/PROJECT_SPECIFICATION.pdf` (add the original PDF there). It requires React.js
and FastAPI, a LangGraph supervisor with Fundamental, Technical, News and Risk agents, PostgreSQL, JWT auth, Plotly
charts, source links and timestamps, downloadable reports, evaluation of calculation accuracy, citation quality and
reliability, and deployment with HTTPS and CORS. When this prompt and the PDF disagree, the PDF wins.

Three differentiators (already built; protect them, do not add more):
1. **Claim Ledger**: every report line is `FACT`, `CALCULATED` or `INTERPRETATION`, linked to evidence and checked
   by a Verifier. Unverifiable claims are blocked from the report.
2. **Contradiction Matrix**: cross-agent disagreement is a first-class dashboard object.
3. **Time-Travel Replay**: run research as of a past date (prices only), then score the technical signal against
   what happened next.

## 2. Current state (verified by running, not assumed)
Built and tested: auth (JWT, argon2), market data service with validation and DB snapshot cache, indicator and ratio
library, four agents, LangGraph supervisor with bounded retries, verifier, Markdown report, research / claims /
contradictions / watchlist / preferences APIs, React dashboard, evaluation harness, production hardening
(config guards, JSON logs, auth rate limit, per-user quotas, stale-task recovery), production Compose + Caddy.

Verified: backend tests 89 passing (87 on SQLite; 2 more need `TEST_DATABASE_URL`, verified on PostgreSQL 16);
frontend 9 tests passing, `npm run build` passes; payload shapes checked against the TypeScript types.

**NOT verified (treat as unknown until you test them):**
- Live yfinance. Financial row labels used: "Total Revenue", "Operating Income", "Net Income", "Total Debt",
  "Stockholders Equity" / "Total Equity Gross Minority Interest", plus `info` keys.
- Live Google News RSS feed parsing.
- The Anthropic LLM adapter (`services/llm.py`, model `claude-sonnet-5-5`); offline `TemplateLLM` is the default.
- The dashboard in a real browser, and the Content-Security-Policy in `deploy/Caddyfile` against Plotly.
- `docker compose` (dev and prod), Caddy, and HTTPS issuance.
- No real evaluation has been run. The only run was on synthetic data and proves the harness works, not the product.

## 3. Repo structure
```
veritas-equity-research/
├── AGENT_MASTER_PROMPT.md           this file
├── README.md                        run, layout, evaluation, deploy, status
├── docker-compose.yml               dev: db + backend + frontend
├── docker-compose.prod.yml          prod: db + backend + frontend + caddy (only 80/443 public)
├── .env.example  .env.production.example  .gitignore
├── .github/workflows/ci.yml         backend (SQLite), backend-postgres, frontend (test + build)
├── deploy/Caddyfile                 HTTPS, security headers, /api reverse proxy
├── docs/
│   ├── DEPLOYMENT.md                runbook: first deploy, smoke test, backup, limits
│   └── PROJECT_SPECIFICATION.pdf    (add the original spec here)
├── backend/
│   ├── Dockerfile  requirements.txt  requirements-dev.txt  pytest.ini  alembic.ini
│   ├── alembic/versions/            0001 schema, 0002 market_snapshots, 0003 task metrics + claim refs
│   ├── app/
│   │   ├── main.py                  app, CORS, access log, /health, /ready, lifespan (prod guard, stale tasks)
│   │   ├── core/                    config (+ validate_production), database, security, logging, ratelimit
│   │   ├── models/entities.py       10 tables (users, research_tasks, agent_results, source_documents,
│   │   │                            research_reports, saved_stocks, claims, contradictions,
│   │   │                            evaluation_runs, market_snapshots)
│   │   ├── schemas/                 claims.py (ledger contract), agents.py (agent outputs), research.py (API)
│   │   ├── data/universe.py         the 20 NSE tickers + search
│   │   ├── tools/                   PURE functions: indicators, risk, fundamentals, registry (run_tool)
│   │   ├── services/                market_data, validation, news, llm, verifier, report, research
│   │   │                            (task executor), maintenance
│   │   ├── agents/                  base (ClaimBuilder), fundamental, technical, news, risk, contradictions
│   │   ├── graph/workflow.py        LangGraph: plan -> [fundamental|technical|news] -> risk -> verify -> report
│   │   ├── api/                     auth, stocks, research, workspace (watchlist, preferences), deps
│   │   └── evaluation/              run (CLI), metrics, reference (independent calcs), drills, replay,
│   │                                synthetic (offline providers), audit (scores labelled citation CSV)
│   └── tests/
│       ├── fakes.py                 FakeProvider / FakeNews / article / make_ohlcv / FIN fixtures
│       ├── unit/                    tools vs TA-Lib and hand values, agents, validation, verifier, claims
│       └── integration/             auth, market data, stocks API, workflow, research API, evaluation,
│                                    hardening, migrations, postgres (needs TEST_DATABASE_URL)
└── frontend/                        Vite + React + TypeScript + Tailwind + Plotly
    └── src/{api,auth,components,lib,pages}   client + types, matrix logic, panels, charts, pages
```
Delete `frontend/node_modules` if present (leftover from an interrupted install; it is gitignored).

Naming note: the data model uses `FACT` / `CALCULATED` / `INTERPRETATION`; reports and the dashboard show them as the
short display tags `FACT` / `CALC` / `AI`. That is intentional, not an inconsistency.

## 4. Architecture in one paragraph
`POST /research` creates a task and runs `execute_task` in the background. The LangGraph workflow warms the data
cache, runs the Fundamental, Technical and News agents in parallel (each with its own DB session and bounded retries on
`ProviderError`), then Risk (which also detects contradictions), then the Verifier, then the report builder. Agents
compute numbers only through `app/tools` and emit claims through `ClaimBuilder`; the LLM only writes summaries.
Results, claims, contradictions and the report are persisted. The frontend polls `/research/{id}` then loads the
report, claims, contradictions and per-agent output.

## 5. Non-negotiable invariants (never break; every change must keep these tests green)
1. **The LLM never does arithmetic or retrieval.** All numbers come from `app/tools`. LLM output containing a number
   not in the facts it was given is rejected (`numbers_grounded`) and replaced by the template text.
2. **Only verified claims appear in a report.** FACT quotes must be literal substrings of the stored
   `source_documents.content_excerpt` (use `fact_line` / `last_close_line` helpers). CALCULATED claims are created by
   running the tool and must reproduce through `run_tool`. INTERPRETATION claims may only cite FACT/CALCULATED claims
   that are themselves verified.
3. **Never invent to fill a gap.** Missing or failed data becomes `unavailable` plus a limitation. Only `ProviderError`
   is retried; any other exception marks that agent `failed` and the rest continue.
4. **Replay is honest.** Financials and news are not point-in-time; replay skips news, warns about financials, and
   only the technical signal is calibrated.
5. **Indicator conventions match TA-Lib** (SMA-seeded EMA, Wilder RSI, TA-Lib MACD seeding). Tests compare to TA-Lib
   and hand-computed values within 1e-6; keep them.
6. **Tests never touch the network.** Use `tests/fakes.py` or `evaluation/synthetic.py`.
7. **One API worker** (in-process rate limiter and background tasks). Do not claim horizontal scaling.
8. No secrets in the repo. Production refuses unsafe config (`validate_production`).
9. Report text always includes the not-investment-advice line; no buy/sell recommendations anywhere.

## 6. Working standards
- Name the real problem and real user before changing anything. Inspect the actual code, tests and data before
  deciding. Label every claim you have not verified by running it.
- Build the smallest complete end-to-end solution and define observable proof (a test, command output or metric).
- Choose new technology only for a demonstrated need. Do not add peer comparison, PDF export, queues, caches or new
  services unless a phase below calls for it or the spec requires it.
- Preserve existing behaviour, tests and audit trail. Add or update tests with every change; never weaken a test to
  make it pass.
- Professional names for files, folders, branches, functions and deliverables. No casual or throwaway names.
- Do not package deliverables as zip files. Report findings and diffs as text.
- Be direct and concise. Prefer working artifacts over explanations. No speculative output.

## 7. Phases
**Phase 0: read-only verification. Make no changes. Then stop and wait for my approval.**
1. Read `README.md`, `docs/DEPLOYMENT.md`, `backend/app/graph/workflow.py`, `services/verifier.py`,
   `services/market_data.py`, `agents/*.py`.
2. Run: `cd backend && pip install -r requirements.txt -r requirements-dev.txt && pytest -q`;
   `cd frontend && npm ci && npm test && npm run build`.
3. Report: test results, anything that differs from section 2, risks you see, and a short plan for phases 1 to 5.

**Phase 1: live verification** (after approval). With network access:
- Run one real ticker through yfinance: `GET /stocks/TCS/prices` and `/financials`. Check that every field the
  Fundamental agent reads is populated for at least 5 tickers; fix label mismatches in `YahooProvider`.
- Parse a real Google News RSS response; fix `GoogleNewsRssProvider` if needed. Keep the provider interface unchanged.
- If an API key is available, exercise `AnthropicLLM`; confirm the grounding guard and fallback work.
- Done when: a real task for TCS completes with `evidence.percent == 100`, and the findings are listed as text.

**Phase 2: real evaluation.** `cd backend && python -m app.evaluation.run --provider yahoo --news google
--out eval_output --pause 2 --usd-per-mtok <rate>` (first with `--tickers TCS`). Label `citation_audit_sample.csv`
with me, then `python -m app.evaluation.audit eval_output/citation_audit_sample.csv`.
Done when: `evaluation_report.md` exists from real data with every metric reported, including failures. Do not tune
code to make metrics look better; fix real bugs and say so.

**Phase 3: browser check.** Run backend and frontend, register, run research, click every tab, download Markdown,
try replay, try the watchlist. Fix real defects with tests where practical. Done when the flow works with no console errors.

**Phase 4: deploy.** Follow `docs/DEPLOYMENT.md` on a host with a domain. Complete its smoke test, including the
Charts tab (adjust the CSP in `deploy/Caddyfile` only if Plotly is blocked). Done when HTTPS works and the smoke test passes.

**Phase 5: documentation.** Write `docs/LIMITATIONS_AND_FUTURE_WORK.md` from the real evaluation results: what
failed, what is not covered (peer comparison, PDF export, news sentiment accuracy, single worker, unofficial data
sources), and prioritised enhancements. Update `README.md` status.

## 8. Commands
```
docker compose up --build                                   # dev stack (API :8000, app :5173)
cd backend && pytest -q                                     # 87 pass + 2 skipped without Postgres
TEST_DATABASE_URL=postgresql+psycopg2://user:pass@host/db pytest -q tests/integration/test_postgres.py   # disposable DB only
cd backend && alembic upgrade head                          # DATABASE_URL must be set
cd frontend && npm test && npm run build
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

## 9. How to report back
After each phase: what you changed (file list and diff summary as text), the exact commands you ran and their
results, what is still unverified, and the next step. If you are blocked or a decision changes scope, stop and ask one
specific question.
