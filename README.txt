===============================================================================
 MULTI-AGENT STOCK RESEARCH ANALYST
 AI-powered stock research using specialized agents
===============================================================================

Current version : 0.1.0  (Module 1 of 10 complete)
Status          : Module 1 - User Authentication and Research Workspace - DONE

-------------------------------------------------------------------------------
1. PROJECT OVERVIEW
-------------------------------------------------------------------------------
A full-stack web application (React + FastAPI + PostgreSQL) for researching
publicly traded stocks. When finished, several AI agents will each analyse
one aspect of a company:

  - fundamental analysis
  - technical analysis
  - news and sentiment
  - risk

A LangGraph Supervisor agent will coordinate them and combine their findings
into one report with sources and timestamps.

The project is built one module per week (10 modules). This README describes
only what is implemented so far.

Note: this software is for research and education. It does not give
investment advice.

-------------------------------------------------------------------------------
2. MODULE 1 - USER AUTHENTICATION AND RESEARCH WORKSPACE
-------------------------------------------------------------------------------
What works now:
  - Register with email and password. Passwords are hashed with Argon2id;
    the plain password is never stored.
  - Log in and receive a JWT access token (valid for 60 minutes).
  - Every workspace endpoint requires a valid token. Each user sees only
    their own data.
  - Preferences: default market (NSE, BSE, NYSE, NASDAQ) and analysis
    period (1M, 3M, 6M, 1Y, 2Y, 5Y).
  - Watchlist: add, list and remove saved stocks. Duplicates are prevented.
  - Research history: lists the user's research tasks, newest first, with
    pagination.
  - React web app with Register, Login and a protected Workspace page.
  - Complete database schema for the whole project (7 tables), created by an
    Alembic migration.

Limitations (planned for later modules):
  - Ticker FORMAT is checked, but whether the company really exists is
    checked only from Module 2 (market data).
  - Research history stays empty until Module 7 starts creating research
    tasks.

-------------------------------------------------------------------------------
3. OBJECTIVES OF MODULE 1
-------------------------------------------------------------------------------
  - Secure user accounts with JWT authentication.
  - A personal workspace (preferences, watchlist, history) for every user.
  - A backend, frontend and database foundation that all later modules
    build on.
  - The database schema finalized, as required by Milestone 1.

-------------------------------------------------------------------------------
4. TECHNOLOGIES USED
-------------------------------------------------------------------------------
Backend  : Python 3.11+, FastAPI, Pydantic, SQLAlchemy 2, Alembic,
           PyJWT, pwdlib (Argon2id), Uvicorn
Database : PostgreSQL 16 (main), SQLite (optional for quick local runs and
           for tests)
Frontend : React 19, Vite, JavaScript, Tailwind CSS, React Router
Testing  : pytest + FastAPI TestClient; Vitest + React Testing Library
Tooling  : Docker Compose (database), GitHub Actions (CI), ESLint

-------------------------------------------------------------------------------
5. FOLDER STRUCTURE
-------------------------------------------------------------------------------
stock-research-analyst/
  backend/
    app/
      main.py              FastAPI app: CORS, routes, /health
      core/                config.py, database.py, security.py
      models/              database tables (__init__.py) and allowed values (enums.py)
      schemas/             request/response shapes and validation
      services/            business logic (users, watchlist, research history)
      api/deps.py          "who is the logged-in user?" dependency
      api/routes/          auth.py, users.py, watchlist.py, research.py
    alembic/               database migrations (versions/0001_initial_schema.py)
    tests/                 85 automated backend tests
    alembic.ini
    pytest.ini
    requirements.txt       runtime packages
    requirements-dev.txt   runtime + test packages
    .env.example           template for your local .env file
  frontend/
    src/
      api/client.js        all calls to the backend
      auth/                login state, protected routes
      components/          Watchlist, Preferences, Research history, UI parts
      pages/               AuthPage (login/register), WorkspacePage
      test/                15 automated frontend tests
    public/favicon.svg
    index.html, package.json, package-lock.json, vite.config.js, eslint.config.js
    .env.example
  docs/
    architecture.md        how the system fits together
    database-schema.md     all tables and columns
    sprints/module-01.md   backlog, task status, review, known issues
    test-reports/module-01-test-report.md
  .github/workflows/ci.yml automatic tests on every push
  docker-compose.yml       local PostgreSQL database
  .gitignore
  README.txt

-------------------------------------------------------------------------------
6. PREREQUISITES
-------------------------------------------------------------------------------
  - Python 3.11 or newer      check with:  python --version
  - Node.js 20.19 or newer    check with:  node --version
  - Git                       check with:  git --version
  - Docker Desktop (recommended, for PostgreSQL)
    No Docker? You can use SQLite instead (see step 7.2, Option B).

-------------------------------------------------------------------------------
7. INSTALLATION AND SETUP
-------------------------------------------------------------------------------
7.1 Start the database (Option A - PostgreSQL with Docker, recommended)
    From the project folder:
        docker compose up -d
    Check it is running:
        docker compose ps         (STATUS should say "healthy")

7.2 Backend
    cd backend

    Create and activate a virtual environment:
      Windows (PowerShell):  python -m venv .venv
                             .venv\Scripts\Activate.ps1
      macOS / Linux:         python3 -m venv .venv
                             source .venv/bin/activate

    Install packages:
        pip install -r requirements-dev.txt

    Create your environment file:
      Windows:      copy .env.example .env
      macOS/Linux:  cp .env.example .env

    Open .env and set JWT_SECRET_KEY to a long random value. Generate one with:
        python -c "import secrets; print(secrets.token_urlsafe(48))"

    Option B (no Docker): in .env, change DATABASE_URL to
        DATABASE_URL=sqlite:///./stock_research.db

    Create the database tables:
        alembic upgrade head

7.3 Frontend (in a second terminal)
    cd frontend
    npm install

    Only if your backend is NOT on http://localhost:8000, copy .env.example
    to .env and edit VITE_API_BASE_URL.

-------------------------------------------------------------------------------
8. HOW TO RUN
-------------------------------------------------------------------------------
Terminal 1 (backend, virtual environment active):
    cd backend
    uvicorn app.main:app --reload
  -> API:               http://localhost:8000
  -> Interactive docs:  http://localhost:8000/docs
  -> Health check:      http://localhost:8000/health

Terminal 2 (frontend):
    cd frontend
    npm run dev
  -> Open http://localhost:5173 in your browser.

Try it: create an account, change your preferences, add RELIANCE (NSE) to
the watchlist, sign out and sign back in.

API endpoints (all under /api/v1):
  POST   /auth/register           create account
  POST   /auth/login              form fields: username (= email), password
  GET    /auth/me                 current user                 [token needed]
  GET    /users/me/preferences    read preferences             [token needed]
  PUT    /users/me/preferences    update preferences           [token needed]
  GET    /watchlist               list saved stocks            [token needed]
  POST   /watchlist               {"ticker": "TCS", "market": "NSE"}
                                                               [token needed]
  DELETE /watchlist/{id}          remove a saved stock         [token needed]
  GET    /research/history        ?limit=20&offset=0           [token needed]

Tip: in http://localhost:8000/docs, click "Authorize". Enter your email in the
"username" box and your password, and you can try every endpoint in the
browser.

-------------------------------------------------------------------------------
9. HOW TO RUN THE TESTS
-------------------------------------------------------------------------------
Backend (from backend/, virtual environment active):
    pytest
  -> uses a temporary in-memory SQLite database; nothing to set up.
  Against PostgreSQL instead (create an empty database first):
    Windows (PowerShell):
      $env:TEST_DATABASE_URL="postgresql+psycopg://stockapp:stockapp@localhost:5432/stock_research_test"; pytest
    macOS / Linux:
      TEST_DATABASE_URL=postgresql+psycopg://stockapp:stockapp@localhost:5432/stock_research_test pytest
  Warning: the test database's tables are dropped and recreated. Never point
  TEST_DATABASE_URL at your real database.

Frontend (from frontend/):
    npm test          automated tests
    npm run lint      code style checks
    npm run build     production build

On GitHub, all of the above runs automatically on every push (Actions tab).

-------------------------------------------------------------------------------
10. EXPECTED OUTPUT
-------------------------------------------------------------------------------
  pytest         ->  85 passed
  npm test       ->  Tests  15 passed (15)
  /health        ->  {"status":"ok","database":"ok"}
  Browser        ->  Sign-in page; after registering, a workspace with
                     Watchlist, Preferences and Research history cards.
                     Research history shows "No research yet" (expected
                     until Module 7).

-------------------------------------------------------------------------------
11. CURRENT DEVELOPMENT STATUS
-------------------------------------------------------------------------------
  [x] Module 1  User Authentication and Research Workspace
  [ ] Module 2  Stock Search and Market Data Collection
  [ ] Module 3  Fundamental Analysis Agent
  [ ] Module 4  Technical Analysis Agent
  [ ] Module 5  News and Sentiment Analysis Agent
  [ ] Module 6  Risk Analysis Agent
  [ ] Module 7  Supervisor Agent and Multi-Agent Orchestration
  [ ] Module 8  AI-Powered Research Report Generation
  [ ] Module 9  Dashboard and Research History
  [ ] Module 10 Testing, Integration and Deployment

Known issues: see docs/sprints/module-01.md

-------------------------------------------------------------------------------
12. FUTURE MODULE INTEGRATION
-------------------------------------------------------------------------------
  - Module 2 adds stock search and price-history endpoints. Watchlist tickers
    will then also be checked against real market data.
  - Modules 3-6 add the analysis agents. Their structured results are stored
    in the existing agent_results table.
  - Module 7 creates research_tasks. The history endpoint and the History card
    built in Module 1 will display them without changes.
  - Module 8 fills research_reports and source_documents.
  - Module 9 extends the React app; Module 10 adds evaluation and deployment
    to the existing CI pipeline.
  - The user's preferences (market, analysis period) become the default
    values for every new research request.

-------------------------------------------------------------------------------
SECURITY NOTES
-------------------------------------------------------------------------------
  - Never commit .env files. .gitignore already excludes them.
  - The database credentials in docker-compose.yml are for your own computer
    only.
  - The app refuses to start with ENVIRONMENT=production unless
    JWT_SECRET_KEY has been changed from the placeholder.
===============================================================================
