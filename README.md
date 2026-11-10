# Veritas Equity Research Platform

Multi-agent, evidence-audited equity research for NSE-listed stocks (React, FastAPI, LangGraph, PostgreSQL).

Every sentence in a report is a typed claim: `FACT` (sourced data), `CALC` (reproducible computation, stored as
`CALCULATED`) or `AI` (interpretation, stored as `INTERPRETATION`). A verifier blocks any claim it cannot check, and cross-agent disagreements are shown in a
contradiction matrix instead of being buried in prose.

## Run
```
cp .env.example .env
docker compose up --build   # API http://localhost:8000/docs, app http://localhost:5173
```
Local development:
```
cd backend  && pip install -r requirements.txt -r requirements-dev.txt && pytest -q
cd frontend && npm ci && npm test && npm run dev
```

## Layout
- `backend/app/core` config, security (argon2, JWT), database
- `backend/app/models`, `schemas` 10 tables and the claim and agent contracts
- `backend/app/tools` validated indicator, risk and ratio functions (no LLM arithmetic)
- `backend/app/agents` fundamental, technical, news, risk; contradiction detector
- `backend/app/graph` LangGraph supervisor with bounded retries
- `backend/app/services` market data, news, LLM, verifier, report, task executor
- `backend/app/api` auth, stocks, research, watchlist and preferences
- `frontend/src` dashboard: search, status, charts, contradiction matrix, claims drill-down, history, watchlist

## Live verification scripts
- `scripts/phase1_live_verification.py` runs the real yfinance and Google News providers end-to-end for a fixed set of tickers and prints evidence coverage (uses live network; not collected by pytest, which runs only `backend/tests`).
- `scripts/phase1_field_scan.py` scans all 20 universe tickers and reports which financial fields the Fundamental agent retrieves from live yfinance.

## Deploy
See `docs/DEPLOYMENT.md`: `docker-compose.prod.yml` runs Caddy (automatic HTTPS), the React app, the API and PostgreSQL
on one host, with only ports 80 and 443 public.

## Evaluation
```
cd backend
python -m app.evaluation.run --provider yahoo --news google --out eval_output --usd-per-mtok <rate>   # real run, 20 tickers
python -m app.evaluation.run --score-audit eval_output/citation_audit_sample.csv                       # after labelling
python -m app.evaluation.run --provider synthetic --news synthetic --tickers TCS,INFY,ITC             # harness self-test only
```
Produces `evaluation_report.md`, `results.json`, `citation_audit_sample.csv` (label the `supported` column
yes / partial / no) and `evaluation.db`. Metrics: calculation agreement with independent references,
citation coverage and correctness, completion rate, latency, cost per report, report completeness,
five failure drills, and replay calibration of the technical signal.

## Status
Backend, dashboard, evaluation harness and production deployment config complete. Verified on PostgreSQL 16 (migrations, concurrent workflows). Next: live-API verification, the real 20-ticker evaluation run, a first deploy.
