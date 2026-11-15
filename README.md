# Module 1 – User Authentication & Research Workspace
Multi-Agent Stock Research Analyst · **React + Tailwind · FastAPI · PostgreSQL · SQLAlchemy · Pydantic · JWT · bcrypt**

```
module1/
├── backend/            FastAPI app (app/), tests (tests/), requirements.txt, .env.example
│   └── app/            config · database · models · schemas · security (bcrypt+JWT) · deps (auth) ·
│                       catalog (tickers/markets/periods) · market_data · workflow · routers/{auth,research,watchlist,preferences}
├── frontend/           React (Vite) + Tailwind: Register, Login, Dashboard (Preferences, Start research, Watchlist, History, Report)
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
cd backend && pytest -q                                   # 45 tests, SQLite by default
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

## HTTPS (guide: "over HTTPS")
Never run production over plain HTTP. Put the app behind TLS (see `Caddyfile`, automatic certificates), then set
`COOKIE_SECURE=true`, a random `SECRET_KEY`, and `EXPOSE_TOKEN_IN_BODY=false`. With `COOKIE_SECURE=true` the app also sends
HSTS and refuses to start with the default secret. Locally (`http://localhost`) `COOKIE_SECURE=false` is fine.

## Things to know
* **Research workflow is a Module 1 placeholder.** It does the real bookkeeping (task → status updates → saved report →
  failures) but the "analysis" is price statistics. `MARKET_DATA_PROVIDER=demo` (default) uses **synthetic, clearly-labelled**
  prices so it works offline; set `yahoo` for real Yahoo Finance daily closes (needs internet; failures are recorded as
  *Failed* tasks). Later modules replace `workflow._analyse` with the multi-agent pipeline.
* The ticker list in `catalog.py` is a validated sample (~70 symbols). Replace it with a market-data search API when ready.
* Tables are auto-created on startup for convenience; use Alembic migrations for real deployments.
* Not included (beyond the guide): login rate-limiting/lockout, email verification, password reset.
