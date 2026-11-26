# Module 1 + Milestones 1 & 2 – Authentication, Research Workspace, Market Data, Indicators & Four Research Agents
Multi-Agent Stock Research Analyst · **React + Tailwind + Plotly · FastAPI · PostgreSQL · SQLAlchemy · Pydantic · JWT · bcrypt · Google/Apple OIDC**

```
module1/
├── backend/            FastAPI app (app/), tests (tests/), requirements.txt, .env.example
│   └── app/            config · database · models · schemas · security (bcrypt+JWT) · deps (auth) ·
│                       catalog (tickers/markets/periods) · market_data (OHLCV/profile/financials) · validation · sources · oauth · workflow ·
│                       news_data · financial_dataset (Kaggle CSV) · analysis/ (indicators, ratios, sentiment, rules) ·
│                       agents/ (fundamental, technical, news, risk + schemas) · routers/{auth,research,watchlist,preferences,market,analysis}
├── frontend/           React (Vite) + Tailwind: Register, Login (+ Google/Apple), Dashboard (Stock search & chart, Preferences, Start research, Watchlist, History, Report)
├── database/schema.sql PostgreSQL DDL (also auto-created on startup)
├── docker-compose.yml  local PostgreSQL        Caddyfile  HTTPS reverse-proxy example
```

## Run it (follows the guide's Section 9 order)
```bash
# 1. PostgreSQL (Docker) – or use any Postgres and edit DATABASE_URL
docker compose up -d

# 2. Backend  (http://localhost:8000, interactive docs at /docs)
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                    # then set SECRET_KEY
uvicorn app.main:app --reload --port 8000

# 3. Frontend (http://localhost:5173 – proxies /api to the backend)
cd frontend && npm install && npm run dev
```
Open http://localhost:5173 → **Register → Login → Dashboard**.

## Tests
```bash
cd backend && pytest -q                                   # 170+ tests, SQLite by default
TEST_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/stockresearch_test pytest -q   # on PostgreSQL
```
Covers validation, hashing, duplicate email, wrong credentials, tampered / expired / `alg:none` / foreign-key tokens,
CSRF, per-user isolation (history, reports, watchlist, preferences), browser-supplied `user_id` being ignored, duplicate
watchlist prevention, preferences, failed workflows, and the full registration-to-dashboard flow.

## How each part of the guide is implemented
| Guide section | Where / how |
|---|---|
| **1 Registration** – name, email, password, confirm; React form → FastAPI; validate email + password; duplicate check; bcrypt; store in `users`; success message | `frontend/src/pages/Register.jsx`, `routers/auth.py::register`, `schemas.py::RegisterRequest`, `security.py::hash_password`. Only `password_hash` is stored. Duplicate → 409 (case-insensitive + DB unique constraint for races). |
| **2 Login** – email, password, button; creds to FastAPI; email lookup; hash verify; token; dashboard; clear error | `pages/Login.jsx`, `auth.py::login`. Wrong email *or* password → `Invalid email or password.` (no user enumeration; bcrypt runs either way). HTTPS: see below. |
| **3 JWT** – id + expiry only; sent to frontend; secure storage; verify signature + expiry; deny missing/invalid/expired | `security.py` (claims: `sub`, `iat`, `exp`, random `csrf` nonce – no personal data). **HTTP-only, SameSite=Lax cookie** (`Secure` when `COOKIE_SECURE=true`) **+ CSRF** (`X-CSRF-Token` must match the signed claim on POST/PUT/DELETE). `Authorization: Bearer` is also accepted (Swagger/Postman). `deps.py::get_current_user` → 401 "sign in again"; frontend redirects to login with that message. |
| **4 Research history** – company+ticker, market, period, date, status, open report; task per research; status updates; failures recorded; user-only endpoint | `models.ResearchTask/ResearchReport`, `routers/research.py`, `workflow.py` (Pending → Processing → Completed/Failed, `error_message` on failure), `ResearchHistory.jsx` (live polling) + `ReportModal.jsx`. `GET /api/research` filters by the **JWT's** user id; other users' tasks → 404. |
| **5 Watchlist** – search name/ticker, add, view, remove, research from saved | `routers/watchlist.py`, `catalog.py` (validated ticker list), `Watchlist.jsx`. Unique `(user_id, ticker)` prevents duplicates; user id from JWT. |
| **6 Preferences** – markets NSE/BSE/NASDAQ/NYSE; periods 1M/3M/6M/1Y/5Y; dropdowns; load on open; save; pass to workflow; provider validation | `routers/preferences.py`, `user_preferences` table, `Preferences.jsx`. Research falls back to saved prefs; `catalog.validate_research_request` checks market + ticker format + supported period; provider symbols `RELIANCE.NS`, `.BO`, plain US tickers; period → data range (`1Y` ≈ 1 year of prices). |
| **7 Database** – users, saved_stocks (+ tasks/reports); PK, FK, unique, indexes | `models.py` / `database/schema.sql`: PKs, FKs (`ON DELETE CASCADE`), `UNIQUE(email)`, `UNIQUE(user_id,ticker)`, `UNIQUE(task_id)` on reports, CHECK constraints, indexes on `user_id`, `(user_id, created_at)`, `status`. |
| **8 Frontend ↔ backend** – React, Tailwind, FastAPI, Python, JWT, bcrypt, PostgreSQL, SQLAlchemy, Pydantic | All used as listed; every request: React → FastAPI (Pydantic validation + auth) → SQLAlchemy/PostgreSQL → JSON → React state. |
| **9 Implementation order / testing** | Tests above + a browser end-to-end run (register → login → dashboard, access control, logout). |

## API summary
`POST /api/auth/register|login|logout` · `GET /api/auth/me` · `GET /api/options` · `GET|PUT /api/preferences` ·
`GET /api/stocks/search?q=&market=` · `GET|POST /api/watchlist` · `DELETE /api/watchlist/{id}` · `POST /api/watchlist/{id}/research` ·
`GET|POST /api/research` · `GET /api/research/{id}` · `GET /api/research/{id}/report` · `GET /api/health`
`GET /api/stocks/{market}/{ticker}/history|profile|financials` · `GET /api/stocks/sources` ·
`GET /api/analysis/{market}/{ticker}/{fundamental|technical|news|risk|all}?period=` · `GET /api/analysis/dataset` ·
`GET /api/auth/providers` · `GET /api/auth/{google|apple}/login` · `GET /api/auth/google/callback` · `POST /api/auth/apple/callback`

## HTTPS (guide: "over HTTPS")
Never run production over plain HTTP. Put the app behind TLS (see `Caddyfile`, automatic certificates), then set
`COOKIE_SECURE=true`, a random `SECRET_KEY`, and `EXPOSE_TOKEN_IN_BODY=false`. With `COOKIE_SECURE=true` the app also sends
HSTS and refuses to start with the default secret. Locally (`http://localhost`) `COOKIE_SECURE=false` is fine.

## Milestone 1 (PDF section 5, weeks 1–2) – what was added
| Milestone 1 task | Where |
|---|---|
| Database schema: `users, research_tasks, agent_results, source_documents, research_reports, saved_stocks` | `models.py`, `database/schema.sql` (+ `oauth_identities`, `user_preferences`). `agent_results` is created now and filled by the agents in Milestone 2+. |
| Stock search (name or ticker) + historical prices + **OHLCV** | `GET /api/stocks/search`, `GET /api/stocks/{market}/{ticker}/history?period=` · `market_data.fetch_ohlcv` |
| Company profile + financial statements | `/profile`, `/financials` (income statement, balance sheet, cash flow; missing fields are listed, never invented) |
| Record data sources and retrieval timestamps | every fetch is stored in `source_documents` (`sources.py`); `GET /api/stocks/sources`; shown under every chart/report |
| Validate missing values, duplicate dates, inconsistent data | `validation.py` – returns clean rows + a report of what was found and what was done (shown on the dashboard) |
| Support NSE/BSE and NYSE/NASDAQ | `catalog.py` (Yahoo symbols `.NS` / `.BO` / plain) |
| Basic stock search interface + price chart | `components/StockExplorer.jsx` – Plotly candlestick + volume, Profile and Financials tabs |

Validation policy: rows with missing O/H/L/C, impossible prices (High < Low, Open/Close outside the day's range, ≤ 0) or negative
volume are removed; duplicate dates keep the last occurrence; out-of-order rows are sorted; close-to-close moves above 40 % are
**flagged, not changed** (could be a split). Fewer than 5 valid rows blocks the analysis. Every action is reported.

## Milestone 2 (PDF section 5, weeks 3–4) – what was added
* **Indicators** (`analysis/indicators.py`): SMA, EMA, RSI (Wilder), MACD (+signal, histogram), log returns, annualised volatility, max drawdown, historical VaR.
  **Validated independently** in `tests/test_m2_calculations.py`: hand-computed values plus pandas/numpy reference implementations.
* **Financial ratios** (`analysis/ratios.py`): growth, CAGR, margins, ROE, ROA, debt/equity, current ratio, FCF margin, cash conversion, P/E, P/B. Every ratio shows its formula and
  inputs; a ratio whose inputs are missing says *Not available* and why. P/E and P/B are refused for synthetic or stale (> 1 year) data.
* **Four agents** with structured Pydantic inputs/outputs (`agents/schemas.py`): **Fundamental**, **Technical**, **News & Sentiment**, **Risk**. Each finding is labelled
  *fact*, *calculated* or *interpretation*. Risk reads the other three and **flags conflicts** (e.g. rising price trend vs falling profit). An agent that cannot run returns
  `Unavailable`/`Failed` with a reason; nothing is invented. Research tasks run all four and store each in `agent_results`.
* **UI**: new tabs *Technical, Fundamentals, News, Risk* in Stock search, and an *Agent analysis* section in the report.
* **Reference dataset**: put the Kaggle CSV at `backend/data/financial_statements.csv` (or set `FINANCIALS_DATASET_PATH`) and run `python -m app.tools.check_dataset` to see which columns were
  recognised. It supplies financial history and peer medians when the live provider has none. Its currency is assumed to be USD.
* **News**: `NEWS_PROVIDER=demo` (SAMPLE headlines, clearly labelled) | `yahoo` (RSS, no key) | `newsapi`.
* Not part of Milestone 2 (Milestone 3+): supervisor/LangGraph orchestration, retries, consolidated report, PDF export.

## Continue with Google / Continue with Apple
Buttons on **Login and Register** → `GET /api/auth/{google|apple}/login` → provider consent screen → `/api/auth/{provider}/callback`
→ same HTTP-only JWT cookie as password login → dashboard. Implementation: `oauth.py`, `routers/auth.py`, `components/SocialButtons.jsx`.
* ID token is **verified** (signature via the provider's JWKS, issuer, audience, expiry, nonce); signed `state` + state cookie block login-CSRF.
* Accounts are matched by provider id, else linked to an existing account with the **same verified email**, else created
  (no password; `password_hash` is NULL). One user can have both Google and Apple linked (`oauth_identities`).
* Without credentials the button redirects back to the login page with a clear "not set up" message; `GET /api/auth/providers` reports what is configured.

**Google setup:** Google Cloud Console → APIs & Services → Credentials → *OAuth client ID* (Web application) → Authorized redirect URI
`http://localhost:5173/api/auth/google/callback` (add your https URL for production) → put the ID/secret in `backend/.env`
(`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`).
**Apple setup** (needs a paid Apple Developer account): create an App ID with *Sign in with Apple*, then a **Services ID** (this is
`APPLE_CLIENT_ID`) with your domain and return URL `https://YOUR-DOMAIN/api/auth/apple/callback`, then a **Key** for Sign in with Apple
(download the `.p8`; Key ID → `APPLE_KEY_ID`, Team ID → `APPLE_TEAM_ID`, file contents → `APPLE_PRIVATE_KEY` with line breaks as `\n`).
Apple does **not** allow `http://localhost`; test it on an https domain (e.g. a tunnel) with `PUBLIC_BASE_URL` and `COOKIE_SECURE=true` set.
The Google and Apple exchange paths are covered by tests with the provider mocked and real token verification against locally generated keys;
the live Google/Apple round-trip needs your credentials and was **not** run here.

**"Google/Apple button does nothing" checklist:** (1) the login page shows *not set up* → the keys are empty in `backend/.env` (the message lists which ones); fill them and **restart the backend**; (2) open the app at `http://localhost:5173`, not `127.0.0.1` (the redirect URI must match exactly); (3) Google says *redirect_uri_mismatch* → add `http://localhost:5173/api/auth/google/callback` in the Google console; (4) Apple will never work on `http://localhost`.

## Login / Register animation
`frontend/src/components/AuthAnimation.jsx` draws a looping candlestick animation (canvas, no video file) in a side panel on both pages. It is illustrative
random data (labelled on screen), hidden on phones, paused when the tab is hidden, and static if the OS asks for reduced motion.
To use a real video instead, put `login.mp4` in `frontend/public/` and replace `<AuthAnimation />` in `AuthLayout.jsx` with
`<video src="/login.mp4" autoPlay loop muted playsInline className="absolute inset-0 h-full w-full object-cover" />`.

## Things to know
* **Research workflow is a Module 1 placeholder.** It does the real bookkeeping (task → status updates → saved report →
  failures) but the "analysis" is price statistics. `MARKET_DATA_PROVIDER=demo` (default) uses **synthetic, clearly-labelled**
  data so it works offline; set `yahoo` for real Yahoo Finance data (needs internet; failures are recorded as
  *Failed* tasks, or HTTP 502 on the market-data endpoints). The Yahoo parsing is tested against mocked responses; Yahoo's unofficial
  endpoints can change or rate-limit, so check the live output once. Later modules replace `workflow._analyse` with the multi-agent pipeline.
* The ticker list in `catalog.py` is a validated sample (~70 symbols). Replace it with a market-data search API when ready.
* Tables are auto-created on startup for convenience; use Alembic migrations for real deployments.
* Not included (beyond the guide): login rate-limiting/lockout, email verification, password reset.
* Existing databases: new tables are created automatically, but `users.password_hash` became nullable – on an existing PostgreSQL
  database run `ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;` (or recreate the DB / use Alembic).
