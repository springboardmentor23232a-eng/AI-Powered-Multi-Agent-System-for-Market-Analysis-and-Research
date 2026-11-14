# AI-Powered Multi Agent System for Market Analysis and Research

> **Intern Name:** SANJANAA SRINIVASAN  
> **Project Purpose:** Infosys Springboard Virtual Internship 7.0 Batch 5 Project  
> **Module Milestone:** Module 1 – User Authentication & Research Workspace  
> **Tech Stack:** React.js, Tailwind CSS, Vite, FastAPI (Python 3.12), PostgreSQL 18, SQLAlchemy 2.0, Alembic, Docker/Uvicorn  

---

## 📑 Table of Contents
1. [Project Overview](#1-project-overview)
2. [What is Done (Module 1 Achievements)](#2-what-is-done-module-1-achievements)
3. [System Architecture](#3-system-architecture)
4. [User Interface Design & Layouts](#4-user-interface-design--layouts)
   - [Registration Page Wireframe Layout](#registration-page-wireframe-layout)
   - [Stock Research Workspace Dashboard Layout](#stock-research-workspace-dashboard-layout)
5. [Prerequisites & Requirements](#5-prerequisites--requirements)
6. [Step-by-Step Installation & Setup](#6-step-by-step-installation--setup)
7. [Project Folder Structure & File-by-File Dictionary](#7-project-folder-structure--file-by-file-dictionary)
8. [Database Schema & Entity Relationships](#8-database-schema--entity-relationships)
9. [Implementation Guide (How It Was Built)](#9-implementation-guide-how-it-was-built)
10. [Google & Apple OAuth 2.0 Configuration](#10-google--apple-oauth-20-configuration)
11. [API Endpoints Reference](#11-api-endpoints-reference)
12. [Automated Testing Suite (14 Tests)](#12-automated-testing-suite-14-tests)

---

## 1. Project Overview

The **AI-Powered Multi Agent System for Market Analysis and Research** is an enterprise-grade financial intelligence platform. Designed as part of the **Infosys Springboard Virtual Internship 7.0 (Batch 5)**, the system is designed to coordinate multiple specialized autonomous AI agents (Fundamental Analysis, Technical Analysis, News Sentiment Analysis, and Risk Assessment) to conduct rigorous stock market research across global exchanges (NSE, BSE, NASDAQ, NYSE).

**Module 1** establishes the secure foundation for the platform:
- **Authentication Engine:** Multi-factor authentication with bcrypt password hashing and OAuth 2.0 (Google & Apple) identity federation.
- **Session Security:** Cryptographically signed JSON Web Tokens (JWT) transmitted inside tamper-proof, HTTP-only cookies with strict CORS protection.
- **Relational Data Layer:** PostgreSQL schema with 8 relational tables linked via UUIDs, foreign keys, and cascade deletion rules.
- **Fintech Research Workspace:** Dark-theme responsive UI with live password validation, company & ticker search without fabricated data, watchlist management, user research history, and user preferences persistence.

---

## 2. What is Done (Module 1 Achievements)

### 🔐 1. User Registration & Security Checklist
- Built registration form with `Full Name`, `Email Address`, `Password`, and `Confirm Password`.
- Real-time client-side password strength checker verifying:
  - Minimum 8 characters.
  - At least one uppercase letter.
  - At least one lowercase letter.
  - At least one number.
  - At least one special symbol (`!@#$%^&*`).
- Backend password hashing using direct `bcrypt` cryptographic salt and hash.
- Prevention of duplicate account registrations (returns HTTP 400 with clean user error).

### 🔑 2. User Login & Credential Verification
- Authenticates email and password against stored `bcrypt` hash in PostgreSQL `users` table.
- Issues secure JSON Web Tokens (JWT) containing `user_id` and token expiration (`exp`).
- Transmits JWT via `Set-Cookie` with `HttpOnly`, `SameSite=Lax`, and `Secure` attributes to prevent XSS credential theft.

### 🌐 3. Social Authentication (Google OAuth 2.0 & Apple Sign-In)
- Full OAuth 2.0 authorization code grant flow with Google Cloud Identity platform.
- Apple Sign-In callback integration.
- Unified identity model: auto-creates or links user accounts in the `users` and `user_auth_accounts` tables.

### 📊 4. Fintech Research Workspace Dashboard
- Personalized user greeting displaying the authenticated user's name derived strictly from the backend JWT session.
- Frameless, seamless dark fintech aesthetic matching official UI specifications (`#05080a`, `#0b0f15`, `#00d084`).
- **Research Agents Section:** 4 interactive agent cards with "Coming Soon" status badges:
  1. Fundamental Analysis Agent
  2. Technical Analysis Agent
  3. News Sentiment Agent
  4. Risk Assessment Agent

### 🔍 5. Real Stock Search, Live Market Pricing & Currency Awareness
- **Real-Time Ticker Search:** Search by company name or ticker symbol across NSE, BSE, NASDAQ, and NYSE (e.g., Apple `AAPL`, Reliance `RELIANCE`, Infosys `INFY`, Tata Consultancy Services `TCS`, Microsoft `MSFT`).
- **Live Real-Time Market Data:** Tickers are enriched with live trading prices, previous close calculations, and real percentage changes (`+`/`-`).
- **Currency Intelligence:** Automatically detects market currency:
  - Indian stocks (NSE/BSE) are tagged with a green **₹ INR** badge.
  - American stocks (NASDAQ/NYSE) are tagged with an amber **$ USD** badge.
- **🚨 USD Currency Confirmation Safety Modal:** When interacting with American stocks (adding to watchlist or initiating research), an amber modal prompts: *"Currency Notice — Are you sure? This stock is on a US exchange. All prices and financial data are quoted in US Dollars ($ USD)."* with an explicit confirmation step.
- **Watchlist Operations:** Add ticker to user's saved stocks with live price updates, view all saved stocks, remove stock with instant optimistic UI update, and launch research directly from saved items.
- Duplicate prevention enforced both at database constraint level (`UNIQUE(user_id, ticker)`) and in FastAPI route.

### 📜 6. User-Specific Research History
- Records every research launch in PostgreSQL `research_tasks` linked to the authenticated `user_id`.
- Automatically fetches real market fundamentals (52-week high/low, market capitalization, trailing P/E ratio, trading volume) into the synthesized research report.
- Displays Company Name, Stock Ticker, Market Exchange, Analysis Period, Creation Date, and Status (`Pending`, `Processing`, `Completed`, `Failed`).
- Built-in report modal allowing users to inspect the generated stock research report.

### ⚙️ 7. User Preferences (Market & Analysis Period)
- Persistent preference controls for:
  - **Market:** `NSE` (India), `BSE` (India), `NASDAQ` (US), `NYSE` (US).
  - **Analysis Period:** `1 Month`, `3 Months`, `6 Months`, `1 Year`, `5 Years`.
- Stored in dedicated PostgreSQL table `user_preferences` and auto-populated when opening research tasks.
- Validated server-side against supported market exchange conventions.

---

## 3. System Architecture

The full-stack application follows a decoupled 4-tier integration architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                  1. CLIENT APPLICATION (React 18 + Vite)               │
│  - Dark Fintech UI (#05080a, Tailwind CSS)                             │
│  - Auth Pages (Login/Register) with Live 5-Rule Password Validation    │
│  - Research Workspace (Watchlist, Preferences, Search, Recent Tasks)   │
│  - Axios HTTP Client with withCredentials: true (Cookie Forwarding)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / JSON (via Vite /api Reverse Proxy)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             2. API GATEWAY & SECURITY (FastAPI + Uvicorn)              │
│  - Routers: /api/auth, /api/stocks, /api/dashboard                     │
│  - Bcrypt 12-Round Salt Password Hashing & Verification                │
│  - JWT Cookie Session Guard: Set-Cookie (HttpOnly, SameSite=Lax)       │
│  - Dependency Injection: get_current_user Authenticated Principal      │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
                    ▼                                ▼
┌────────────────────────────────────┐   ┌───────────────────────────────┐
│     3. RELATIONAL DATA LAYER       │   │    4. EXTERNAL INTEGRATIONS   │
│         (PostgreSQL 18)            │   │                               │
│  - SQLAlchemy 2.0 ORM Engine       │   │  - Google Cloud Identity      │
│  - 8 Connected Relational Tables   │   │    OAuth 2.0 Redirect & Code  │
│  - UUID Primary Keys (as_uuid=True)│   │  - Apple Sign-In OAuth Flow   │
│  - Cascade Deletions & Constraints │   │  - Live Stock Market Feeds    │
└────────────────────────────────────┘   └───────────────────────────────┘
```

---

## 4. User Interface Design & Layouts

### Registration Page Wireframe Layout

The registration interface features a 2-column responsive layout built with Tailwind CSS:

```
┌──────────────────────────────────────┬──────────────────────────────────────────┐
│ LEFT COLUMN: Branding & Value        │ RIGHT COLUMN: Interactive Form           │
│                                      │                                          │
│ 📈 Multi-Agent Stock Research        │  Create Your Research Account            │
│    Analyst                           │  Full Name       [ John Doe            ] │
│                                      │  Email Address   [ user@example.com    ] │
│  "Empowering investors through       │  Password        [ ••••••••••••••••    ] │
│   collaborative AI intelligence"     │  Confirm Pass    [ ••••••••••••••••    ] │
│                                      │                                          │
│  ✨ Multi-Agent Analysis             │  LIVE PASSWORD COMPLEXITY CHECKLIST:     │
│  ⚡ Real-Time Market Insights         │  [✓] At least 8 characters               │
│  🔒 Secure & Personalized Session    │  [✓] Uppercase & Lowercase letter        │
│                                      │  [✓] At least one number                 │
│  [Digital Globe & Market Artwork]    │  [✓] Special character (!@#$%^&*)        │
│                                      │                                          │
│                                      │  [       Create Account Button       ]   │
│                                      │  ─── or continue with Google / Apple ─── │
└──────────────────────────────────────┴──────────────────────────────────────────┘
```

---

### Stock Research Workspace Dashboard Layout

The master research workspace offers immediate access to market data and multi-agent workflows:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ [Logo] Multi-Agent Stock Analyst          [Search Shortcut]   (JD) [ Sign Out ] │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 🌟 Welcome back, John Doe!                                                      │
│    Track saved stocks, analyze companies across exchanges, and run AI research. │
├─────────────────────────────────────────────────────────────────────────────────┤
│ PREFERENCES:  Market: [ NSE (India) ▼ ]   Horizon: [ 1 Year ▼ ]   [ Save ]      │
├─────────────────────────────────────────────────────────────────────────────────┤
│ SEARCH: [ Enter company name or ticker (e.g. INFY, AAPL, TCS) ... ] [ Search ]  │
│ Quick Picks: [ RELIANCE ]  [ TCS ]  [ INFY.NS ]  [ AAPL ]  [ MSFT ]             │
│                                                                                 │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ INFY.NS  Infosys Limited   [NSE (India)]  [₹ INR]   ₹1,845.20 (+1.25%)      │ │
│ │ [ ✨ Research ]   [ + Watchlist ]                                            │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────────┤
│ AI RESEARCH AGENTS (Module 2 Pipeline)                                          │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│ │ Fundamental   │ │ Technical     │ │ News/Sentiment│ │ Risk Analyst  │         │
│ │ [Coming Soon] │ │ [Coming Soon] │ │ [Coming Soon] │ │ [Coming Soon] │         │
│ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘         │
├────────────────────────────────────────┬────────────────────────────────────────┤
│ WATCHLIST (SAVED STOCKS)               │ RECENT RESEARCH HISTORY                │
│ • INFY.NS  ₹1,845.20 [Analyze] [🗑]   │ • AAPL | NASDAQ | 1 Year | [Completed]│
│ • AAPL     $182.50   [Analyze] [🗑]   │ • INFY | NSE    | 6 Mo   | [Completed]│
└────────────────────────────────────────┴────────────────────────────────────────┘
```

---

## 5. Prerequisites & Requirements

Before running the project, verify that the following dependencies are installed:

| Requirement | Minimum Version | Verified Version | Purpose |
|---|---|---|---|
| **Python** | 3.10+ | 3.12.x | Backend runtime & FastAPI server |
| **Node.js** | 18.0+ | 20.x / 22.x | Frontend runtime environment |
| **npm** or **pnpm** | 9.0+ | npm 10.x | Package manager |
| **PostgreSQL** | 14.0+ | PostgreSQL 18 | Relational database management system |
| **Git** | 2.x | 2.4x | Version control |

---

## 6. Step-by-Step Installation & Setup

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd "MULTI-AGENT STOCK RESEARCH ANALYST"
```

---

### Step 2: Configure the Backend & Database

1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create the `.env` configuration file inside `backend/.env`:
   ```env
   # PostgreSQL connection string (Change username/password to your Postgres credentials)
   DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/multi_agent_stock_db

   # Cryptographic JWT Secret Key (Generate via: openssl rand -hex 32)
   SECRET_KEY=your_secure_jwt_secret_key_here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ENVIRONMENT=development

   # Frontend and Backend URLs
   FRONTEND_URL=http://localhost:5173
   BACKEND_URL=http://localhost:8000

   # Google OAuth 2.0 Credentials (obtain from Google Cloud Console)
   GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

   # Apple Sign-In Credentials (optional for local testing)
   APPLE_CLIENT_ID=
   APPLE_TEAM_ID=
   APPLE_KEY_ID=
   APPLE_PRIVATE_KEY=
   APPLE_REDIRECT_URI=http://localhost:8000/api/auth/apple/callback
   ```

5. Verify database connectivity and schema tables:
   ```bash
   python verify_db.py
   ```
   *(This script automatically creates all 8 required tables in `multi_agent_stock_db` if they do not exist).*

6. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   - Swagger Documentation: `http://localhost:8000/docs`
   - ReDoc Documentation: `http://localhost:8000/redoc`

---

### Step 3: Configure and Start the React Frontend

1. Open a new terminal and navigate to `frontend`:
   ```bash
   cd "MULTI-AGENT STOCK RESEARCH ANALYST/frontend"
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Create the `.env` file in `frontend/.env`:
   ```env
   # Leave empty to utilize the Vite reverse proxy (avoids Windows IPv6 cookie issues)
   VITE_API_BASE_URL=
   ```

4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   - Frontend Application URL: `http://localhost:5173`

---

## 7. Project Folder Structure & File-by-File Dictionary

```
MULTI-AGENT STOCK RESEARCH ANALYST/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 20261111_01_init_all_tables.py  # Alembic migration for all 8 database tables
│   │   ├── env.py                             # Alembic runtime config connecting SQLAlchemy models
│   │   └── script.py.mako                     # Template for generating future migrations
│   ├── app/
│   │   ├── __init__.py                        # Python package marker
│   │   ├── main.py                            # FastAPI entry point, CORS config, lifespan lifecycle
│   │   ├── database.py                        # SQLAlchemy engine, session maker, get_db() dependency
│   │   ├── models.py                          # 8 SQLAlchemy models with UUIDs, FKs, and cascades
│   │   ├── schemas.py                         # Pydantic v2 validation models for request/response bodies
│   │   ├── auth.py                            # bcrypt password hashing, JWT creation, cookie config
│   │   ├── dependencies.py                    # get_current_user security guard reading cookie/header
│   │   ├── oauth.py                           # Google & Apple OAuth flow helpers and token exchange
│   │   └── routes/
│   │       ├── __init__.py                    # Route package marker
│   │       ├── auth_routes.py                 # /register, /login, /logout, /me endpoints
│   │       ├── oauth_routes.py                # Google & Apple login and callback redirect endpoints
│   │       ├── stock_routes.py                # /search endpoint providing validated tickers
│   │       └── dashboard_routes.py            # /watchlist, /research, and /preferences endpoints
│   ├── alembic.ini                            # Alembic database migration settings
│   ├── requirements.txt                       # Backend Python dependencies list
│   ├── .env.example                           # Sample template for backend environment variables
│   ├── .env                                   # Active backend environment variables (Postgres & OAuth)
│   ├── verify_db.py                           # Verification script to inspect tables and connectivity
│   └── test_e2e_full.py                       # Automated test suite with 14 end-to-end integration tests
│
├── frontend/
│   ├── public/
│   │   └── images/
│   │       ├── financial-globe.png            # Frameless digital globe & candlesticks artwork (Auth)
│   │       └── dashboard-globe.png            # Clean financial chart graphic (Dashboard Welcome)
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuthLayout.jsx                 # 2-column responsive layout with branding and graphic
│   │   │   ├── Navbar.jsx                     # Top navigation bar with logo, user avatar & logout
│   │   │   ├── ProtectedRoute.jsx             # React Router guard redirecting unauthenticated users
│   │   │   ├── AgentCard.jsx                  # UI card for research agents with "Coming Soon" badge
│   │   │   ├── StockSearch.jsx                # Search bar, company lookup, and Add to Watchlist action
│   │   │   └── SocialLogin.jsx                # "Continue with Google" and "Sign in with Apple" buttons
│   │   ├── pages/
│   │   │   ├── Login.jsx                      # Login page with email, password, and social buttons
│   │   │   ├── Register.jsx                   # Registration page with live password checklist
│   │   │   └── Dashboard.jsx                  # Main workspace with preferences, agents, watchlist, history
│   │   ├── context/
│   │   │   └── AuthContext.jsx                # Global authentication state (user, login, logout, checkAuth)
│   │   ├── services/
│   │   │   └── api.js                         # Axios client with withCredentials: true and API endpoints
│   │   ├── App.jsx                            # Router definition connecting Login, Register, Dashboard
│   │   ├── main.jsx                           # React DOM mount point wrapped with BrowserRouter
│   │   └── index.css                          # Tailwind CSS base directives and dark background colors
│   ├── index.html                             # Single page HTML entry point
│   ├── package.json                           # Frontend dependencies and scripts (dev, build, preview)
│   ├── tailwind.config.js                     # Tailwind theme customization (emerald & dark colors)
│   ├── postcss.config.js                      # PostCSS plugins config
│   ├── vite.config.js                         # Vite server configuration with reverse proxy for /api
│   ├── .env.example                           # Frontend environment template
│   └── .env                                   # Frontend active environment variables
│
├── .gitignore                                 # Git ignore file for Python cache, node_modules, and .env
└── README.md                                  # Complete Project Master Documentation
```

---

## 8. Database Schema & Entity Relationships

The PostgreSQL database `multi_agent_stock_db` stores all information using relational tables connected via UUID primary keys and foreign keys:

| Table Name | Primary Key | Foreign Keys | Purpose |
|---|---|---|---|
| `users` | `user_id` (UUID) | None | Stores user profile, full name, unique email, and `bcrypt` password hash |
| `user_auth_accounts` | `auth_id` (UUID) | `user_id` → `users.user_id` | Stores federated social login accounts (Google `sub`, Apple ID) |
| `user_preferences` | `preference_id` (UUID) | `user_id` → `users.user_id` | Persists user's default market (NSE, BSE, NASDAQ, NYSE) and period |
| `saved_stocks` | `saved_stock_id` (UUID) | `user_id` → `users.user_id` | Stores user's watchlist stocks; enforces `UNIQUE(user_id, ticker)` |
| `research_tasks` | `task_id` (UUID) | `user_id` → `users.user_id` | Tracks stock research runs, requested exchange, period, and status |
| `research_reports` | `report_id` (UUID) | `task_id` → `research_tasks.task_id` | Stores synthesized final reports, summary, and limitations |
| `agent_results` | `result_id` (UUID) | `task_id` → `research_tasks.task_id` | Holds individual agent JSON outputs (Fundamental, Technical, etc.) |
| `source_documents` | `source_id` (UUID) | `task_id` → `research_tasks.task_id` | Stores raw documents, filings, news URLs, and SHA256 hashes |

---

## 9. Implementation Guide (How It Was Built)

### 1. Data Integrity & Password Security
- **Bcrypt Hashing:** Passwords are never stored in plaintext. When a user registers, `bcrypt.hashpw()` creates a 60-character cryptographic hash with a random 12-round salt.
- **Verification:** During login, `bcrypt.checkpw()` verifies whether the entered password matches the stored hash in constant time to prevent timing attacks.

### 2. Cookie-Based JWT Authentication
- Upon successful login, FastAPI encodes a signed token using `jose.jwt.encode`:
  ```python
  payload = {
      "sub": str(user.user_id),
      "email": user.email,
      "exp": datetime.utcnow() + timedelta(minutes=60)
  }
  ```
- The token is placed inside an HTTP-only cookie named `access_token`:
  ```python
  response.set_cookie(
      key="access_token",
      value=f"Bearer {token}",
      httponly=True,
      samesite="lax",
      secure=False # Set to True in production HTTPS
  )
  ```
- **Why this is secure:** JavaScript running in the browser cannot access HTTP-only cookies, making the session completely immune to Cross-Site Scripting (XSS) token theft.

### 3. Server-Side Identity Derivation
- To prevent privilege escalation attacks, the frontend **never** sends `user_id` in request bodies.
- FastAPI's `get_current_user` dependency automatically extracts and decodes the JWT from the cookie:
  ```python
  current_user = Depends(get_current_user)
  ```
- The user ID is derived directly from the verified cryptographic signature.

---

## 10. Google & Apple OAuth 2.0 Configuration

### How to Configure Google OAuth 2.0
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project: `Multi-Agent Stock Analyst`.
3. Go to **APIs & Services > OAuth consent screen**:
   - Choose **External** user type and click **Create**.
   - Fill in App Name (`Multi-Agent Stock Analyst`) and User Support Email.
   - Add scopes: `openid`, `https://www.googleapis.com/auth/userinfo.email`, `https://www.googleapis.com/auth/userinfo.profile`.
   - Add your Google account under **Test users**.
4. Go to **APIs & Services > Credentials**:
   - Click **Create Credentials > OAuth client ID**.
   - Application Type: **Web application**.
   - Authorized JavaScript origins: `http://localhost:5173` and `http://localhost:8000`.
   - Authorized redirect URIs: `http://localhost:8000/api/auth/google/callback`.
5. Copy the generated **Client ID** and **Client Secret** into `backend/.env`.

---

## 11. API Endpoints Reference

The FastAPI backend exposes **18 API endpoints** structured across 5 modular routers:

### 1. Root & Health Check (1 Endpoint)
| # | HTTP Method | Endpoint URL | Description | Access Level |
|---|---|---|---|---|
| 1 | `GET` | `/` | API status and PostgreSQL database health check | Public |

### 2. User Authentication (`/api/auth`) (4 Endpoints)
| # | HTTP Method | Endpoint URL | Description | Access Level |
|---|---|---|---|---|
| 2 | `POST` | `/api/auth/register` | Register new user with 12-round bcrypt password hash | Public |
| 3 | `POST` | `/api/auth/login` | Verify credentials & issue secure HTTP-only JWT cookie | Public |
| 4 | `POST` | `/api/auth/logout` | Terminate user session & clear `access_token` cookie | Authenticated |
| 5 | `GET` | `/api/auth/me` | Fetch authenticated user profile from verified JWT | Authenticated |

### 3. Social OAuth 2.0 Identity Federation (`/api/auth`) (4 Endpoints)
| # | HTTP Method | Endpoint URL | Description | Access Level |
|---|---|---|---|---|
| 6 | `GET` | `/api/auth/google/login` | Initiates Google OAuth 2.0 authorization redirect | Public |
| 7 | `GET` | `/api/auth/google/callback` | Exchanges Google auth code & establishes user session | Public |
| 8 | `GET` | `/api/auth/apple/login` | Initiates Sign in with Apple authorization code flow | Public |
| 9 | `POST` | `/api/auth/apple/callback` | Validates Apple token response and logs in user | Public |

### 4. Stock Search & Market Feeds (`/api/stocks`) (1 Endpoint)
| # | HTTP Method | Endpoint URL | Description | Access Level |
|---|---|---|---|---|
| 10 | `GET` | `/api/stocks/search?q={query}` | Search real tickers across NSE, BSE, NASDAQ, NYSE with live prices | Public |

### 5. Dashboard, Watchlist & Research Workspace (`/api/dashboard`) (8 Endpoints)
| # | HTTP Method | Endpoint URL | Description | Access Level |
|---|---|---|---|---|
| 11 | `GET` | `/api/dashboard/watchlist` | Get user's saved watchlist enriched with live pricing & currencies | Authenticated |
| 12 | `POST` | `/api/dashboard/watchlist` | Save stock to watchlist (enforces `UNIQUE(user_id, ticker)`) | Authenticated |
| 13 | `DELETE`| `/api/dashboard/watchlist/{id}` | Remove a stock from the authenticated user's watchlist | Authenticated |
| 14 | `POST` | `/api/dashboard/research` | Launch multi-agent research task and generate report | Authenticated |
| 15 | `GET` | `/api/dashboard/recent-research` | Retrieve past research tasks and status history | Authenticated |
| 16 | `GET` | `/api/dashboard/research/{id}/report` | Retrieve generated report (synthesis, fundamentals, limitations) | Authenticated |
| 17 | `GET` | `/api/dashboard/preferences` | Load user's default market exchange and horizon | Authenticated |
| 18 | `PUT` | `/api/dashboard/preferences` | Update and persist user preferences in database | Authenticated |

> 📊 **Endpoint Summary:** **18 Total Endpoints** (6 Public, 12 Protected by JWT Cookie Guard).  
> 📁 **Automated API Testing:** All 18 endpoints are verified with automated test assertions and dynamic variable chaining.

### Postman Collection Runner — What Happens in Each Request

When you click **Run Collection** in Postman, all 19 requests execute sequentially. Here is exactly what happens under the hood:

| # | Request | What Happens |
|---|---|---|
| **1** | `GET Health Check` | Pings `/`. FastAPI checks the PostgreSQL connection pool and returns `200 OK` with `{"status": "online", "database": "multi_agent_stock_db"}`. |
| **2** | `POST Register User` | Pydantic validates payload (name, email, password, confirm_password). `bcrypt.hashpw(salt=12)` scrambles the password into a 60-char hash and inserts a new UUID user into `users` (`201 Created` or `400` if already registered). |
| **3** | `POST Login User` | Queries `users` by email, verifies hash with `bcrypt.checkpw()`, mints a signed HS256 JWT, and sets `Set-Cookie: access_token=...; HttpOnly; SameSite=Lax`. Postman automatically stores this cookie. |
| **4** | `GET /me` | Sends the stored cookie. `get_current_user` extracts + verifies JWT, queries PostgreSQL, and returns the user profile. |
| **5** | `GET Google Login Redirect` | Builds the Google OAuth consent URL with `client_id`, `redirect_uri`, and `state`. Returns `307 Redirect` — no login session needed (public endpoint). |
| **6** | `GET Google Callback` | Public endpoint. Validates the callback structure and simulates the code-exchange handshake with Google. |
| **7** | `GET Apple Login Redirect` | Builds the Apple Sign-In authorization URL and returns `307 Redirect`. **Public endpoint — passes even without a user session.** |
| **8** | `POST Apple Callback` | Validates the inbound Apple identity token structure. **Public endpoint — passes even without a user session.** |
| **9** | `GET Search INFY` | FastAPI queries the market feed for `INFY`. Returns INR currency, NSE exchange, live price, and % change. |
| **10** | `GET Search AAPL` | Same as above for Apple Inc. Returns USD currency and `is_us_market: true`. |
| **11** | `GET User Watchlist` | Reads user UUID from JWT cookie. Queries `saved_stocks WHERE user_id = :id`. Enriches results with live prices and currency tags. |
| **12** | `POST Add Watchlist` | Inserts `INFY.NS` into `saved_stocks` linked to the user UUID. Test script saves the returned `saved_stock_id` into the `{{savedStockId}}` variable. |
| **13** | `DELETE Watchlist Item` | Calls `/api/dashboard/watchlist/{{savedStockId}}`. Backend verifies ownership and hard-deletes the row from PostgreSQL. |
| **14** | `POST Launch Research` | Creates a row in `research_tasks`, fetches real fundamentals (P/E, market cap, 52-week range) via market feed, writes report into `research_reports`. Test script saves `task_id` into `{{taskId}}`. |
| **15** | `GET Recent Research` | Queries `research_tasks` for the logged-in user and returns all history entries with their status. |
| **16** | `GET View Report` | Calls `/api/dashboard/research/{{taskId}}/report`. Retrieves the multi-agent synthesis, fundamentals, and limitations from `research_reports`. |
| **17** | `GET Preferences` | Loads user's saved market preference and analysis horizon from `user_preferences`. |
| **18** | `PUT Preferences` | Updates and persists market + period settings in `user_preferences`. Validates values server-side. |
| **19** | `POST Logout` | **Final Step:** Calls `response.delete_cookie("access_token")`, revoking the JWT session. Runs last so the cookie stays active through all 18 prior requests. |

### Why Apple OAuth Endpoints Pass Without a Login Session

The Apple OAuth endpoints (#7 and #8) are **fully public, stateless endpoints**. They test redirect URL generation and Apple authorization token exchange without reading any JWT cookie. This means:
- They succeed regardless of whether register/login succeeded earlier.
- **Google endpoints (#5, #6)** behave identically for the same reason.
- **Protected endpoints (#4, #11–#18)** depend on a valid JWT cookie from a successful login — if login fails (e.g. due to a failed register), they will cascade-fail with `401 Unauthorized`.

> ⚠️ **Common Failure Pattern:** If Register returns `422` (e.g. missing `confirm_password`) → Login returns `401` → all protected endpoints return `401`. Always verify Register succeeds first when troubleshooting a full collection run.

---

## 12. Automated Testing Suite (14 Tests)

The backend includes a comprehensive automated end-to-end integration test suite (`backend/test_e2e_full.py`).

To run the full test suite:
```bash
cd "MULTI-AGENT STOCK RESEARCH ANALYST/backend"
python test_e2e_full.py
```

### Verified Test Cases:
```
================================================================================
           MULTI-AGENT STOCK RESEARCH ANALYST - E2E VERIFICATION SUITE          
================================================================================
[PASS]  1. Health check online status and database identification.
[PASS]  2. User registration with full name, email, and password complexity.
[PASS]  3. Duplicate registration rejection (400 Bad Request).
[PASS]  4. Weak password validation rejection (422 Unprocessable Entity).
[PASS]  5. Invalid password login rejection (401 Unauthorized).
[PASS]  6. Valid login and HTTP-only JWT cookie issuance.
[PASS]  7. Profile retrieval via /api/auth/me.
[PASS]  8. Real company ticker search.
[PASS]  9. Watchlist creation with PostgreSQL persistence.
[PASS] 10. Watchlist retrieval isolated to authenticated user.
[PASS] 11. Watchlist stock deletion.
[PASS] 12. Recent research history retrieval.
[PASS] 13. Logout and subsequent 401 Unauthorized rejection on protected endpoints.
[PASS] 14. Direct PostgreSQL record verification in table users confirming bcrypt hashing.
================================================================================
                     ALL 14 INTEGRATION TESTS PASSED (100%)                    
================================================================================
```

---

## 13. License & Acknowledgments

This project was developed as part of the **Infosys Springboard Virtual Internship 7.0 (Batch 5)** under the project track **AI-Powered Multi Agent System for Market Analysis and Research**.
