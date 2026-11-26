# Understanding the Stock Research Analyst Module 1 code

This note explains the main request flow in plain language. It is intended to help you understand, test, and present the implementation.

## How a request moves through the app

1. A person uses a form or button in the React frontend.
2. `frontend/src/api.js` sends the request to FastAPI and includes browser cookies.
3. FastAPI validates the incoming data with the Pydantic classes in `backend/app/schemas.py`.
4. Protected routes use `backend/app/dependencies.py` to verify the session JWT and identify the signed-in user.
5. The route reads or changes records through SQLAlchemy models in `backend/app/models.py`.
6. PostgreSQL stores the data, and FastAPI returns a response for React to display.

## Backend files

- `config.py`: reads environment variables such as the database URL, cookie settings, Yahoo Finance configuration, and Google OAuth credentials.
- `database.py`: creates the SQLAlchemy engine and provides a database session to API routes.
- `models.py`: describes the PostgreSQL tables (including `market_data_records`, `users`, `user_preferences`, `saved_stocks`, `research_tasks`, `research_reports`, `agent_results`, `source_documents`) and their relationships.
- `schemas.py`: validates request bodies and shapes API responses for auth, workspace, OHLCV bars, company profiles, financial statements, and market snapshots.
- `security.py`: hashes and verifies passwords, creates JWTs, and prepares authentication cookies.
- `dependencies.py`: checks the signed-in user and protects cookie-based write requests against CSRF.
- `oauth.py`: configures the Google OpenID Connect client.
- `services/yahoo_finance.py`: coordinates direct data retrieval from Yahoo Finance via the `yfinance` library (no API key required, strictly zero artificial/simulated data). Provides:
  - Search by company name or ticker symbol via `yf.Search`
  - Historical stock price retrieval via `yf.Ticker(symbol).history()`
  - OHLCV collection (Open, High, Low, Close, Volume, Timestamp)
  - Company profiles via `ticker.info` and `ticker.fast_info` (officers, valuation, P/E, market cap)
  - Financial statements via `ticker.income_stmt`, `ticker.balance_sheet`, and `ticker.cashflow`
  - Data source labels (`Yahoo Finance via yfinance`) & ISO-8601 UTC retrieval timestamps
  - Multi-market ticker normalization (NSE `.NS`, BSE `.BO`, NASDAQ, NYSE)
  - Meaningful error handling on failure (StockNotFoundError, NoHistoricalDataError, RateLimitError, MarketDataProviderError)
- `routers/auth.py`: handles registration, email/password login, Google login, current-session lookup, and logout.
- `routers/workspace.py`: handles preferences, stock search, watchlists, research tasks, and report retrieval.
- `routers/market_data.py`: exposes `/api/market` endpoints for search, historical prices, profiles, financials, and recording snapshots to PostgreSQL.
- `main.py`: creates the FastAPI application, configures middleware, and registers the route groups.

## Frontend files

- `src/App.jsx`: renders the registration/login screens and the signed-in workspace, sidebar navigation, watchlist, preferences, and research history.
- `src/MarketDataView.jsx`: provides the interactive market intelligence dashboard:
  - Multi-market company and ticker search
  - Quick stock selectors (TCS, Reliance, Infosys, Apple, Microsoft, NVIDIA)
  - Real-time and historical price summary cards
  - SVG interactive price chart with volume bars and hover crosshair
  - Complete OHLCV table with CSV download
  - Comprehensive company profile and executive leadership directory
  - Switchable financial statement tables (Income Statement, Balance Sheet, Cash Flow, Key Ratios)
  - Audit trail badges showing data source and UTC retrieval timestamp
  - Database snapshot recorder and saved collections viewer
- `src/api.js`: keeps HTTP calls in one place so components do not repeat request details.
- `src/main.jsx`: mounts the React application.
- `src/styles.css`: contains the responsive page styling.

## Why the user ID is not sent by the browser

A browser can be modified by its user, so the backend must not trust a `user_id` field supplied by the frontend. The protected route reads the user ID from the verified JWT instead. That is how watchlists, preferences, and research history stay associated with the correct account.

## What the research-history feature does today

Creating a research task saves a row with `Pending` status. The tables for reports, agent results, and source documents are ready to store later work, but this Module 1 app does not run the multi-agent analysis engine. A later module must process a task and update its status before a completed report can be shown.

## Database setup note

If all seven tables already exist in your Neon or Supabase PostgreSQL database, do not run `create_tables.py` again. Point `backend/.env` at that same database. The startup `create_all()` call is safe for existing tables, but it is not a schema migration tool.

## Before presenting the project

Try the registration, login, logout, Google login (if configured), preference saving, stock lookup, watchlist, and research-task flow yourself. Be ready to explain how password hashing, JWT verification, CSRF checks, foreign keys, and user-specific queries work.
