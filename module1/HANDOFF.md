# HANDOFF – Multi-Agent Stock Research Analyst (Infosys Virtual Internship project)

Paste this file (and upload `module1-handoff.zip`) into a new Claude chat and say:
**"Continue this project from HANDOFF.md – finish the 'Still to do' list, then test and give me the zip."**

---

## 1. What the project is
Full-stack web app: **React (Vite) + Tailwind + Plotly · FastAPI · SQLAlchemy · Pydantic · PostgreSQL (SQLite for local dev) · JWT + bcrypt**.
Reference spec: the PDF "AI-Powered Multi Agent System for Market Analysis and Research" (milestones; upload it again in the new chat).
Reference dataset: Kaggle "Financial Statements of Major Companies (2009-2023)" by rish59
https://www.kaggle.com/datasets/rish59/financial-statements-of-major-companies2009-2023
**It could not be downloaded in the previous chat (Kaggle was blocked), and its real column names were never seen.**
The loader auto-matches column names; the user must put the CSV at `backend/data/financial_statements.csv`
and run `cd backend && python -m app.tools.check_dataset` to see what was recognised.

User is on Windows/PowerShell, has NO Docker -> uses `DATABASE_URL=sqlite:///./dev.db` in `backend/.env`.
Run: backend `uvicorn app.main:app --reload --port 8000` (venv in `backend/.venv`), frontend `cd frontend && npm install && npm run dev` -> http://localhost:5173.

## 2. DONE and verified (before this handoff)
**Module 1** (original, user-supplied): register, login (JWT in HTTP-only cookie + CSRF), research history, watchlist, preferences, 8 DB tables.
**Milestone 1** (added by me, tested): schema (`agent_results`, `source_documents`), OHLCV + company profile + financial statements endpoints
(`/api/stocks/{market}/{ticker}/history|profile|financials`, `/api/stocks/sources`), data validation (`validation.py`: missing, duplicate, inconsistent,
negative volume, extreme moves), source + retrieval timestamp logging, Plotly candlestick chart + Profile/Financials tabs (`StockExplorer.jsx`).
`MARKET_DATA_PROVIDER=demo` (default, clearly-labelled SYNTHETIC data) or `yahoo` (real; parsing tested only with mocks, never run live).
**Continue with Google / Apple** (code + tests done): `app/oauth.py`, routes in `routers/auth.py`
(`/api/auth/providers`, `/api/auth/{google|apple}/login`, `/google/callback` GET, `/apple/callback` POST), `components/SocialButtons.jsx`,
`oauth_identities` table, ID-token verification (signature/iss/aud/exp/nonce), signed state + state cookie, link by verified email.
**Login/Register animation:** `AuthAnimation.jsx` (canvas candlesticks, side panel, hidden on mobile, reduced-motion safe).
**Dark/light theme + magic cursor + animations** (done by a sub-agent, verified in a real browser with Playwright): `ThemeContext.jsx` (`useTheme()`),
`plotlyTheme.js`, `ThemeToggle.jsx`, `MagicCursor.jsx` (with a "cursor" on/off toggle), CSS keyframes/`.reveal`/`.skeleton`/`.spinner` in `index.css`,
dark overrides as `.dark .<utility>` rules, `PriceChart.jsx` theme-aware. Not verified: contrast with a tool, sparkle trail visually.
**Presentation script** for the mentor (a Claude Doc): "Project Presentation Script – Multi-Agent Stock Research Analyst (Module 1 + Milestone 1)".

## 3. Milestone 2 – backend BUILT this session (all `backend/app/…`)
(Built; now fully tested - see section 4.)
* `analysis/indicators.py` – sma, ema, rsi (Wilder), macd, log returns, annualised volatility, max drawdown, historical VaR, `percentile`, `rolling_returns_pct`.
* `analysis/ratios.py` – `compute_ratios()` (growth, CAGR, margins, ROE, ROA, D/E, current ratio, FCF margin, cash conversion, P/E, P/B; each ratio carries formula, inputs, kind calculated|reported, reason_unavailable).
* `analysis/sentiment.py` – transparent rule-based news sentiment + event detection. `analysis/technical_rules.py` – `detect_conditions`, `overall_bias`.
* `financial_dataset.py` – Kaggle CSV loader (alias column matching, duplicates, `match_company`, `series_for`, `peers`). `tools/check_dataset.py` – CLI check.
* `news_data.py` – providers: `demo` (labelled SAMPLE headlines, default), `yahoo` (RSS, no key), `newsapi` (needs `NEWSAPI_KEY`). Config: `NEWS_PROVIDER`, `NEWSAPI_KEY`, `FINANCIALS_DATASET_PATH`.
* `agents/schemas.py` (Pydantic input/output models), `agents/context.py` (`build_context`: fetch+validate prices once, >=1Y warm-up, logs sources),
  `agents/fundamental.py`, `technical.py`, `news.py`, `risk.py`, `agents/__init__.py` (`run_agent`, `run_all`; a crashing agent becomes status "Failed").
  Fundamental source priority: real provider financials > dataset > synthetic (flagged). P/E, P/B only when price + financials are real, current (<=1 yr old) and same currency.
  Risk agent: volatility, max drawdown, VaR, historical-percentile scenarios, financial/sector flags, **cross-agent conflict detection**, data gaps, deterministic level.
* `routers/analysis.py` – `GET /api/analysis/{market}/{ticker}/{fundamental|technical|news|risk|all}?period=` and `GET /api/analysis/dataset`. Registered in `main.py` (version 2.0.0).
* `workflow.py` – research tasks now run all four agents, store each in `agent_results`, and put `agents` into the report `content`.
* Quick smoke check (demo mode, AAPL 1Y): all four agents returned Completed with sensible summaries.

## 4. STATUS – Milestone 2 is COMPLETE (tests + UI + docs)
* Backend tests: **170+ pass** (`pytest -q`): includes `test_m2_calculations.py` (independent hand/pandas/numpy checks), `test_m2_agents.py` (agents, dataset loader with a tmp CSV, news providers with mocked HTTP, conflicts, endpoints, workflow rows), and new Google/Apple redirect tests.
* Frontend: `AgentPanels.jsx` + `TechnicalChart.jsx` + new tabs (Technical, Fundamentals, News, Risk) in `StockExplorer.jsx`, "Agent analysis" in `ReportModal.jsx`. Verified in a real Chromium (Playwright) in light and dark; no console errors.
* Google/Apple diagnosis: the buttons "do nothing" because no credentials are in `backend/.env`; the login page now says which variables are missing (local mode only). With fake credentials the real chain was shown to 303-redirect to accounts.google.com with the state cookie. A live login was NOT run.
* README, `.env.example` (NEWS_PROVIDER, NEWSAPI_KEY, FINANCIALS_DATASET_PATH), requirements (pandas/numpy for tests) updated.

### Next (Milestone 3, not started): Supervisor/LangGraph orchestration, retries, consolidated report, PDF export.
### Optional polish: real Kaggle CSV check (`python -m app.tools.check_dataset`), live Yahoo/NewsAPI run, Plotly bundle splitting.

## 5. Decisions / rules to keep
* **Never invent data.** Missing -> "not available" with a reason. Synthetic demo data (prices, financials, SAMPLE news) is always labelled.
* Milestone 2 = ratios, indicators, the four agents with structured outputs, validation tests. **Supervisor / LangGraph / retries / consolidated report / PDF export are Milestone 3+ – do not build them yet.**
* Findings must distinguish fact / calculated / interpretation; interpretations are rule-based and are not investment advice or predictions.
* The dataset's units/currency are unknown: only unit-free ratios are computed from it; its currency is assumed USD (stated as a limitation); P/E from stale (>1 yr) financials is refused.
* Be upfront with the user about what was not verified live (Google/Apple round trip, Yahoo live data, Kaggle CSV).

## 6. Known gaps / honest caveats
* Kaggle CSV never seen -> column mapping is best-effort; run `check_dataset` and fix `ALIASES` in `financial_dataset.py` if headers differ.
* No login rate-limiting, email verification, password reset. Tables auto-created (no Alembic). `users.password_hash` is nullable (existing PostgreSQL DBs need `ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;`).
* Ticker catalog (`catalog.py`) is a ~70-symbol sample list.
* Plotly bundle ~1 MB (lazy-loaded; build warns about chunk size).

## 7. File map (important files)
```
module1/
  backend/app/ main.py config.py models.py schemas.py security.py deps.py workflow.py catalog.py
              market_data.py validation.py sources.py news_data.py financial_dataset.py oauth.py
              routers/{auth,research,watchlist,preferences,market,analysis}.py
              analysis/{indicators,ratios,sentiment,technical_rules}.py
              agents/{schemas,context,fundamental,technical,news,risk,__init__}.py
              tools/check_dataset.py
  backend/tests/ conftest.py test_auth.py test_features.py test_market_data.py test_social_login.py   (104 tests, SQLite)
  backend/data/  (put financial_statements.csv here)      backend/.env.example
  frontend/src/  App.jsx main.jsx ThemeContext.jsx plotlyTheme.js index.css api.js AuthContext.jsx
                 pages/{Login,Register,Dashboard}.jsx
                 components/{AuthLayout,AuthAnimation,SocialButtons,ThemeToggle,MagicCursor,StockExplorer,PriceChart,
                             Preferences,StartResearch,Watchlist,ResearchHistory,ReportModal}.jsx
  database/schema.sql  docker-compose.yml  Caddyfile  README.md  HANDOFF.md
```
