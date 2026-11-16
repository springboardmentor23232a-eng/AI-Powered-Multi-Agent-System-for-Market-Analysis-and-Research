# SAI ANALYSIS: Multi-Agent Stock Research Analyst

**Technical Documentation, Architectural Specification, and Developer Handbook**  
*Document Version: 1.0.0 | System Milestone: Module 1 Complete (Tasks 1 through 6)*

---

## Table of Contents

- [1. Project Title and Introduction](#1-project-title-and-introduction)
- [2. Project Overview](#2-project-overview)
- [3. Key Features — Detailed Explanation](#3-key-features--detailed-explanation)
  - [3.1 User Registration](#31-user-registration)
  - [3.2 User Login](#32-user-login)
  - [3.3 JWT-Based Authentication](#33-jwt-based-authentication)
  - [3.4 User-Specific Research History](#34-user-specific-research-history)
  - [3.5 Saved Stocks / Watchlists](#35-saved-stocks--watchlists)
  - [3.6 User Preferences](#36-user-preferences)
- [4. Technology Stack](#4-technology-stack)
- [5. System Architecture](#5-system-architecture)
  - [5.1 Component Topology Diagram](#51-component-topology-diagram)
  - [5.2 Authentication and Authorization Flow Diagram](#52-authentication-and-authorization-flow-diagram)
- [6. Complete Project Folder Structure](#6-complete-project-folder-structure)
  - [6.1 Repository Directory Tree](#61-repository-directory-tree)
  - [6.2 File-by-File Technical Directory](#62-file-by-file-technical-directory)
- [7. Backend Architecture — Deep Technical Explanation](#7-backend-architecture--deep-technical-explanation)
  - [7.1 Core Subsystems](#71-core-subsystems)
  - [7.2 Master API Routes Registry](#72-master-api-routes-registry)
- [8. Frontend Architecture — Deep Technical Explanation](#8-frontend-architecture--deep-technical-explanation)
  - [8.1 Single-Page Application Design](#81-single-page-application-design)
  - [8.2 UI Components and Presentation Layer](#82-ui-components-and-presentation-layer)
- [9. Database Architecture](#9-database-architecture)
  - [9.1 Entity-Relationship (ER) Diagram](#91-entity-relationship-er-diagram)
  - [9.2 Table Specifications and Schemas](#92-table-specifications-and-schemas)
  - [9.3 Safe Database Inspection Queries](#93-safe-database-inspection-queries)
- [10. Complete Application Workflows](#10-complete-application-workflows)
  - [Workflow A: User Registration](#workflow-a-user-registration)
  - [Workflow B: User Authentication and Login](#workflow-b-user-authentication-and-login)
  - [Workflow C: Protected Workspace Access](#workflow-c-protected-workspace-access)
  - [Workflow D: User Logout](#workflow-d-user-logout)
  - [Workflow E: Research Task Execution and History](#workflow-e-research-task-execution-and-history)
  - [Workflow F: Stock Watchlist Management](#workflow-f-stock-watchlist-management)
  - [Workflow G: User Market and Period Preferences](#workflow-g-user-market-and-period-preferences)
- [11. API Documentation](#11-api-documentation)
- [12. Environment Setup](#12-environment-setup)
- [13. Environment Variables and Configuration](#13-environment-variables-and-configuration)
- [14. Running the Project](#14-running-the-project)
- [15. Testing and Quality Assurance](#15-testing-and-quality-assurance)
- [16. Manual Testing Guide](#16-manual-testing-guide)
- [17. Error Handling and Troubleshooting](#17-error-handling-and-troubleshooting)
- [18. Security Implementation](#18-security-implementation)
- [19. Current Implementation Status](#19-current-implementation-status)
- [20. Known Limitations](#20-known-limitations)
- [21. Future Enhancements](#21-future-enhancements)
- [22. Developer Maintenance Guide](#22-developer-maintenance-guide)
- [23. Important Commands Reference](#23-important-commands-reference)
- [24. Project Completion Summary](#24-project-completion-summary)

---

## 1. Project Title and Introduction

### Project Name
**SAI ANALYSIS: Multi-Agent Stock Research Analyst**

### Professional Description
An enterprise-grade, asynchronous financial intelligence and stock research platform combining strict multi-tenant user authentication, personalized market watchlists, user-configured market preferences, and persistent multi-asset research execution histories.

### Project Background and Problem Statement
Retail investors, equity analysts, and institutional researchers regularly navigate disparate platforms to gather market data, monitor watchlists, examine historical prices, and preserve analytical records. Most existing market applications suffer from three critical architectural shortcomings:
1. **Lack of Session Isolation**: Financial watchlists and historical research tasks are frequently stored in ephemeral client storage or insecure single-user databases without cryptographic user boundary enforcement.
2. **Brittle Upstream Ingestion**: Financial tools often couple presentation directly with raw third-party market APIs, failing to validate OHLCV candle continuity, volume anomalies, or exchange-ticker mismatches before rendering reports.
3. **Rigid Analysis Parameters**: Users are locked into hardcoded time horizons or geographic exchanges, preventing personalized workflows across domestic and international markets.

### Purpose and Solution
SAI ANALYSIS was engineered to resolve these challenges by providing:
- **Cryptographic Security and Identity**: Stateless JSON Web Token (JWT) authentication delivered via secure, HTTP-only, SameSite cookies alongside standard Bearer token header fallback.
- **Strict Relational Persistence**: Complete PostgreSQL data schema with foreign-key integrity, cascade deletions, and database-level unique constraints preventing duplicate watchlist entries and cross-user data leakage.
- **Dual Analytical Workspace**: An integrated dashboard featuring real-time stock lookup, embedded SVG sparklines, interactive historical price charts, verified OHLCV trading candles, personal watchlists, and persistent research task histories with detailed analytical modal viewers.
- **Dynamic Parameterization**: Per-user preferences persisted in PostgreSQL, enabling users to customize default target exchanges (`NSE`, `BSE`, `NASDAQ`, `NYSE`) and historical analysis horizons (`1mo`, `3mo`, `6mo`, `1y`, `5y`).

### Intended Audience and Scope
The platform is designed for financial engineers, equity researchers, and software engineering teams. Within the scope of **Module 1 (User Authentication & Research Workspace)**, the system implements all user onboarding, cryptographic authentication, session validation, watchlist tracking, research task execution, structured report inspection, and preference management capabilities.

---

## 2. Project Overview

SAI ANALYSIS is structured as a decoupled client-server architecture. The frontend is a React single-page application built on Vite and styled with Tailwind CSS, utilizing a dark crimson theme. The backend is an asynchronous FastAPI service utilizing SQLAlchemy 2.0 ORM connected to a PostgreSQL relational database.

```
+-------------------------------------------------------------------------------+
|                             CLIENT / BROWSER                                  |
|  React 19 SPA (Vite Dev Server :5173 / Production Nginx)                      |
|  - Auth State & Protected Routing (/register, /login, /dashboard)             |
|  - Dual Workspace: Watchlist Grid & Research Execution History                |
|  - Interactive SVG Charts, Sparklines, and Fundamental Metric Grids           |
+---------------------------------------+---------------------------------------+
                                        |
                  HTTP / REST (JSON)    | Reverse Proxy (/api -> :8000)
                  Cookies: credentials  | Authorization: Bearer <token>
                                        v
+-------------------------------------------------------------------------------+
|                           FASTAPI BACKEND (:8000)                             |
|  Application Router & Middlewares:                                            |
|  - CORS Security Policy (Whitelisted origins & regex)                         |
|  - Global Exception Handlers (400, 401, 403, 404, 409, 422, 500)              |
|  - Lifespan Engine (Connection verification & automatic table init)           |
|                                                                               |
|  API Layer:                                                                   |
|  ├── /api/auth        -> Registration, Login, Logout, Profile (/me)           |
|  ├── /api/stocks      -> Symbol Search, Fundamental Overview, OHLCV History   |
|  ├── /api/watchlist   -> Add Stock, List Watchlist, Remove Saved Stock        |
|  ├── /api/research    -> Execute Research Task, User History, Report Details  |
|  └── /api/preferences -> Retrieve Preferences, Update Market & Period         |
+-------------------+---------------------------------------+-------------------+
                    |                                       |
    SQLAlchemy 2.0  | Connection Pool (psycopg2)            | yfinance API
                    v                                       v
+---------------------------------------+   +-----------------------------------+
|         POSTGRESQL DATABASE           |   |       YAHOO FINANCE API           |
|  Database: stock_research_db          |   |  - Real-time quote streaming      |
|  ├── users                            |   |  - Balance sheet & fundamentals   |
|  ├── user_preferences                 |   |  - Historical OHLCV candles       |
|  ├── saved_stocks                     |   +-----------------------------------+
|  ├── research_tasks                   |
|  └── research_reports                 |
+---------------------------------------+
```

### End-to-End Application Lifecycle
1. **User Onboarding**: The user navigates to `/register` and submits account details. The frontend enforces real-time client validation (name length, email syntax, password complexity, confirmation matching).
2. **Backend Persistence**: FastAPI receives the payload, validates it via Pydantic v2 schemas, verifies email uniqueness against PostgreSQL, hashes the password via bcrypt (12 rounds of salt), and inserts a record into the `users` table.
3. **Session Issuance**: Upon `/login`, the backend verifies credentials, generates a signed HMAC-SHA256 JWT, sets an HTTP-only cookie (`access_token`) with `SameSite=lax` configuration, and returns user profile metadata.
4. **Dashboard Access**: The frontend `/dashboard` route executes an authentication handshake against `/api/auth/me`. If valid, the workspace initializes; if invalid or expired, the user is redirected to `/login`.
5. **Preference Synchronization**: On dashboard load, the client queries `/api/preferences`. If no record exists, the backend initializes default preferences (`NSE`, `1mo`). Saved market and duration values dynamically populate stock execution controllers.
6. **Watchlist Operations**: Users query stocks via debounced autocomplete against `/api/stocks/search`, preview fundamentals, and save tickers to `/api/watchlist`. Duplicate insertions are rejected at both business logic and database constraint levels (`uq_user_saved_ticker`).
7. **Research Execution**: Users initiate analysis tasks via `/api/research/tasks`. The backend records a `ResearchTask` in `Pending` state, transitions to `Processing`, validates ticker and market compatibility, fetches live fundamentals and historical OHLCV candles via `yfinance`, generates a `ResearchReport`, updates the task to `Completed`, and persists the full analytical artifact.

---

## 3. Key Features — Detailed Explanation

### 3.1 User Registration
- **User Workflow**: Users provide `Full Name`, `Email Address`, `Password`, and `Confirm Password` on the registration page.
- **Client Validation**: Real-time feedback powered by [useRegistrationForm.js](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/hooks/useRegistrationForm.js). Checks minimum 2 characters for names, standard RFC 5322 email formatting, and passwords containing at least 8 characters, 1 uppercase letter, and 1 numeric digit. A multi-segment password strength meter visualizes entropy.
- **Backend Schema Enforcement**: [UserRegisterRequest](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/schemas/auth.py) strips leading/trailing whitespace, validates email syntax via `email-validator`, and uses Pydantic root validators to ensure password matching.
- **Duplicate Prevention**: The backend queries `users.email = payload.email.lower()`. If a record exists, an HTTP 409 Conflict exception is raised.
- **Password Security**: Passwords are encrypted using `bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))`. Raw passwords are never persisted or logged.
- **Database Insertion**: Inserts into `users` (`user_id`, `full_name`, `email`, `password_hash`, `created_at`).
- **Response**: Returns HTTP 201 Created with `{ status: "success", message: "User registered successfully.", data: { user_id, email, full_name, role, created_at } }`.

### 3.2 User Login
- **User Workflow**: Users supply registered email and password credentials on [LoginPage.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/pages/LoginPage.jsx).
- **Backend Verification**: [authenticate_user](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/user_service.py) normalizes the email, retrieves the user record, and runs `bcrypt.checkpw()`.
- **Failure Handling**: Invalid emails or mismatched passwords return HTTP 401 Unauthorized with generic error messages preventing user enumeration.
- **Session Issuance**: Generates a cryptographically signed JWT token with a 60-minute default lifetime and dispatches it via a secure cookie.

### 3.3 JWT-Based Authentication
- **Token Structure**: Standard RFC 7519 JWT payload comprising:
  - `sub`: Authenticated user ID (stringified integer).
  - `email`: Authenticated user email address.
  - `iat`: Issued-at UTC timestamp.
  - `exp`: Expiration UTC timestamp (`now + ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Signature Algorithm**: Signed using HMAC-SHA256 (`HS256`) against a server-side `JWT_SECRET_KEY`.
- **Dual-Transport Ingestion**: [dependencies.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/dependencies.py) inspects:
  1. `request.cookies.get("access_token")` (Primary web browser mechanism).
  2. `request.headers.get("Authorization")` matching `Bearer <token>` (API and automated testing fallback).
- **Cookie Security Configuration**:
  - `httponly=True`: Prevents client-side JavaScript access via `document.cookie` (mitigates XSS token extraction).
  - `samesite="lax"`: Mitigates Cross-Site Request Forgery (CSRF) in top-level cross-origin navigations.
  - `secure=False`: Enabled for local HTTP development; set to `True` in production HTTPS deployments.
  - `path="/"`, `max_age=3600`.
- **Route Guarding**: Protected endpoints declare `Depends(get_current_user)`. Unauthenticated or invalid requests receive HTTP 401 Unauthorized with `WWW-Authenticate: Bearer` headers.
- **Session Termination**: `/api/auth/logout` sets `response.delete_cookie("access_token")`, revoking client access.

### 3.4 User-Specific Research History
- **Task Creation**: Calling `POST /api/research/tasks` records a `ResearchTask` row referencing `user_id = current_user.user_id`.
- **State Progression**: Task transitions across three states:
  1. `Pending`: Task initialized in database.
  2. `Processing`: Upstream market data retrieval initiated.
  3. `Completed` or `Failed`: Analysis finalized, execution timestamp recorded.
- **Structured Report Artifact**: On success, a `ResearchReport` row is persisted with a 1-to-1 foreign key to `task_id`, containing:
  - `report_content`: Master JSON schema containing overview, history, summary, and metadata objects.
  - `overview_data`: Fundamental metrics (P/E ratio, Market Cap, 52-Week High/Low, Sector, Industry).
  - `history_data`: Array of validated OHLCV candles (timestamp, open, high, low, close, volume).
  - `summary`: Markdown analytical narrative summarizing technical indicators and company business.
  - `limitations`: Analytical disclaimer documenting data source limitations, coverage periods, and trading day counts.
- **Strict Data Isolation**: History retrieval queries execute `db.query(ResearchTask).filter(ResearchTask.user_id == current_user.user_id)`. Users cannot view or query tasks generated by other accounts.
- **Report Inspection**: Clicking an item in the dashboard history list opens [ReportModal.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/components/research/ReportModal.jsx), querying `/api/research/tasks/{task_id}`.

### 3.5 Saved Stocks / Watchlists
- **Adding Stocks**: Calling `POST /api/watchlist` accepts `{ "ticker": "INFY.NS" }`.
- **Validation**: Ticker is cleaned (whitespace stripped, uppercase) and verified via [validate_ticker_symbol](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/validation_service.py).
- **Duplicate Prevention**: Checked before insertion via `db.query(SavedStock).filter(user_id, ticker)`. If present, raises HTTP 409 Conflict. Database schema enforces `UniqueConstraint('user_id', 'ticker', name='uq_user_saved_ticker')`.
- **Multi-Tenant Watchlists**: Different users can save the same ticker independently.
- **Viewing Watchlists**: Calling `GET /api/watchlist` retrieves all tickers saved by the caller, enriched with company name, exchange, and live pricing data.
- **Removing Stocks**: Calling `DELETE /api/watchlist/{saved_stock_id}` checks ownership. If `stock.user_id != current_user.user_id`, access is denied with HTTP 404/403.
- **Cross-Workspace Trigger**: Clicking any watchlist entry automatically populates the search bar, selects the relevant market, and triggers an analytical query.

### 3.6 User Preferences
- **Configurable Options**:
  - `market`: `NSE` (National Stock Exchange of India), `BSE` (BSE Ltd., India), `NASDAQ` (US), `NYSE` (US).
  - `analysis_period`: `1mo` (1 Month), `3mo` (3 Months), `6mo` (6 Months), `1y` (1 Year), `5y` (5 Years).
- **Defaults**: Unconfigured user profiles initialize to `market = "NSE"`, `analysis_period = "1mo"`.
- **Retrieval**: `GET /api/preferences` fetches or creates the caller's preferences.
- **Updating**: `PUT /api/preferences` accepts `{ "market": "NASDAQ", "analysis_period": "1y" }`. Invalid values are rejected with HTTP 422 Unprocessable Content.
- **Persistence**: Persisted in PostgreSQL table `user_preferences` with a unique constraint on `user_id` and automatic `updated_at` timestamps.
- **Workflow Influence**: Loaded preferences dynamically update dashboard state, ensuring all subsequent stock searches and research tasks inherit the user's preferred market and duration.

---

## 4. Technology Stack

| Technology Layer | Tool / Library | Version | Usage in Project | Justification & Architectural Benefit |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend Framework** | React | `^19.0.0` | Client presentation layer | Modern concurrent rendering, fast reconciliation, robust component lifecycle. |
| **Frontend Language** | JavaScript (ES6+ / JSX) | Modern | Application logic and UI components | Native browser compatibility with standard modern syntax. |
| **Build Tool & Dev Server** | Vite | `^8.3.7` | Frontend bundler & dev server | Lightning-fast Hot Module Replacement (HMR) and optimized Rollup production builds. |
| **Client Routing** | React Router DOM | `^7.1.5` | Client-side routing (`BrowserRouter`) | Declarative routing, browser history manipulation, route navigation guards. |
| **Styling Framework** | Tailwind CSS | `^3.4.1` | Utility-first CSS styling | Rapid UI styling, design system tokens (`#060608` pitch black, `#e11d48` crimson). |
| **PostCSS Processor** | PostCSS & Autoprefixer | `^8.4.35` | CSS transformation | Automated CSS vendor prefixing and CSS syntax processing. |
| **Iconography** | Lucide React | `^1.16.0` | UI icons | High-performance, tree-shakeable SVG vector icons with zero external asset overhead. |
| **Frontend Linter** | Oxlint | Modern | Static analysis | High-speed static analysis catching React lifecycle and syntax issues. |
| **Backend Framework** | FastAPI | `>=0.110.0` | REST API layer | High throughput ASGI framework, native async/await, OpenAPI generation. |
| **ASGI Server** | Uvicorn (standard) | `>=0.28.0` | Production ASGI web server | High-performance asynchronous networking based on `uvloop` and `httptools`. |
| **Data Validation** | Pydantic & Pydantic-Settings | `>=2.6.0` | Request validation & settings | Schema enforcement, automatic data coercion, environment variable ingestion. |
| **Email Validation** | email-validator | `>=2.1.0` | Email syntax verification | RFC 5322 syntax validation preventing malformed email registrations. |
| **Relational Database** | PostgreSQL | `14+ / 18` | Persistent relational storage | ACID compliance, robust indexing, foreign key cascade integrity, concurrent isolation. |
| **Database ORM** | SQLAlchemy | `>=2.0.28` | Database modeling & query engine | SQLAlchemy 2.0 type safety, connection pooling, declarative model definitions. |
| **PostgreSQL Driver** | psycopg2-binary | `>=2.9.9` | Low-level PostgreSQL adapter | High-speed C-extension PostgreSQL database driver. |
| **Password Security** | bcrypt | `>=4.1.2` | Password hashing & verification | Industry-standard salt-based hashing algorithm resistant to GPU brute-force attacks. |
| **Authentication Tokens** | PyJWT | `>=2.8.0` | Cryptographic JWT signing | Lightweight, secure RFC 7519 JSON Web Token signing and signature validation. |
| **Financial Market Data** | yfinance | `>=0.2.37` | Real-time & historical quotes | Reliable market data retrieval for Indian (NSE/BSE) and US (NASDAQ/NYSE) equities. |
| **Data Processing** | Pandas | `>=2.2.0` | Financial series transformation | Fast dataframe aggregation, OHLCV candle normalization, missing bar detection. |
| **Numerical Computing** | NumPy | `>=1.26.0` | Metric calculation | Low-level vectorized math for percentage changes, volatility, and volume summaries. |
| **HTTP Client (Testing)** | HTTPX | `>=0.27.0` | Asynchronous test client | High-performance HTTP client used by FastAPI `TestClient` for test suites. |
| **Automated Testing** | Pytest | `>=8.1.0` | Backend unit and integration tests | Robust test execution runner with fixture management and assertion introspection. |
| **Configuration** | python-dotenv | `>=1.0.1` | Local environment loader | Parses `.env` key-value pairs into application runtime environment. |

---

## 5. System Architecture

### 5.1 Component Topology Diagram

```mermaid
flowchart TD
    subgraph Client ["Client Browser Tier"]
        UI["React 19 SPA (Vite)"]
        Router["React Router DOM (/register, /login, /dashboard)"]
        AuthHook["useRegistrationForm Hook"]
        UIComp["Bento Dashboard & Report Modal"]
    end

    subgraph ReverseProxy ["Dev Server / API Proxy Tier"]
        ViteProxy["Vite Proxy (:5173/api -> :8000/api)"]
    end

    subgraph BackendApp ["FastAPI Application Tier (:8000)"]
        Main["FastAPI App Factory (app/main.py)"]
        CORS["CORS Middleware"]
        AuthDep["Security Dependency (get_current_user)"]
        
        subgraph APIRoutes ["REST API Routers"]
            R_Auth["/api/auth"]
            R_Pref["/api/preferences"]
            R_Stock["/api/stocks"]
            R_Watch["/api/watchlist"]
            R_Res["/api/research"]
        end

        subgraph ServiceLayer ["Business Logic & Services Tier"]
            S_Sec["Security Service (bcrypt, PyJWT)"]
            S_User["User Service"]
            S_Pref["Preference Service"]
            S_Stock["Stock Service (yfinance integration)"]
            S_Val["Validation Service"]
            S_Watch["Watchlist Service"]
            S_Res["Research Service"]
        end
    end

    subgraph DatabaseTier ["Persistence Tier (PostgreSQL)"]
        Engine["SQLAlchemy 2.0 Engine & Pool"]
        T_Users[("users")]
        T_Prefs[("user_preferences")]
        T_Watch[("saved_stocks")]
        T_Tasks[("research_tasks")]
        T_Reports[("research_reports")]
    end

    subgraph ExternalServices ["External Data Tier"]
        YF["Yahoo Finance API"]
    end

    %% Client Interactions
    UI --> Router
    Router --> AuthHook
    Router --> UIComp
    UIComp -->|HTTP Requests| ViteProxy
    ViteProxy -->|Proxied REST Calls| Main

    %% Backend Routing & Auth
    Main --> CORS
    CORS --> APIRoutes
    APIRoutes -.->|Token Validation| AuthDep
    AuthDep -->|Cryptographic Verification| S_Sec

    %% Route to Service
    R_Auth --> S_User
    R_Auth --> S_Sec
    R_Pref --> S_Pref
    R_Stock --> S_Stock
    R_Stock --> S_Val
    R_Watch --> S_Watch
    R_Res --> S_Res

    %% Service to DB
    S_User --> Engine
    S_Pref --> Engine
    S_Watch --> Engine
    S_Res --> Engine

    %% Engine to Tables
    Engine --> T_Users
    Engine --> T_Prefs
    Engine --> T_Watch
    Engine --> T_Tasks
    Engine --> T_Reports

    %% Service to External
    S_Stock --> YF
    S_Res --> YF
```

### 5.2 Authentication and Authorization Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser
    participant FE as React Frontend
    participant API as FastAPI Backend
    participant SEC as Security Service
    participant DB as PostgreSQL Database

    Note over User,DB: Phase 1: User Registration
    User->>FE: Fills Full Name, Email, Password
    FE->>FE: Validates Client Rules (Length, Strength, Match)
    FE->>API: POST /api/auth/register (JSON Payload)
    API->>DB: Query users WHERE email = payload.email
    alt Email already registered
        DB-->>API: User Record Exists
        API-->>FE: HTTP 409 Conflict (Email already in use)
        FE-->>User: Displays error alert banner
    else Email is unique
        API->>SEC: hash_password(plain_password)
        SEC-->>API: Returns bcrypt hash ($2b$12$...)
        API->>DB: INSERT INTO users (full_name, email, password_hash)
        DB-->>API: Created user_id
        API-->>FE: HTTP 201 Created (UserResponse JSON)
        FE-->>User: Displays success message & prompts login
    end

    Note over User,DB: Phase 2: User Login & Session Issuance
    User->>FE: Submits Email & Password
    FE->>API: POST /api/auth/login {email, password}
    API->>DB: Query users WHERE email = payload.email
    alt User not found OR password mismatch
        API->>SEC: verify_password(plain, stored_hash)
        SEC-->>API: False
        API-->>FE: HTTP 401 Unauthorized (Invalid credentials)
        FE-->>User: Displays invalid credentials banner
    else Credentials valid
        API->>SEC: verify_password(plain, stored_hash) -> True
        API->>SEC: create_access_token(user_id, email)
        SEC-->>API: Returns Signed JWT (HS256)
        API-->>FE: HTTP 200 OK + Set-Cookie: access_token=... (HttpOnly, SameSite=lax)
        FE->>FE: Store user profile in localStorage('currentUser')
        FE-->>User: Redirects to /dashboard
    end

    Note over User,DB: Phase 3: Protected Workspace Access
    User->>FE: Navigates to /dashboard
    FE->>API: GET /api/auth/me (Cookie automatically sent)
    API->>API: get_current_user Dependency
    alt Missing or Expired Token
        API-->>FE: HTTP 401 Unauthorized
        FE->>FE: Clear localStorage('currentUser')
        FE-->>User: Redirects to /login
    else Token Signature and Expiry Valid
        API->>DB: SELECT * FROM users WHERE user_id = token.sub
        DB-->>API: User row
        API-->>FE: HTTP 200 OK {status: "success", data: UserResponse}
        FE-->>User: Renders personalized dashboard & analytical charts
    end

    Note over User,DB: Phase 4: User Logout
    User->>FE: Clicks Logout button
    FE->>API: POST /api/auth/logout
    API-->>FE: HTTP 200 OK + Delete-Cookie: access_token
    FE->>FE: localStorage.removeItem('currentUser')
    FE-->>User: Redirects to /login
```

---

## 6. Complete Project Folder Structure

### 6.1 Repository Directory Tree

The following directory tree represents the actual structure of the repository:

```text
SAI-ANALYSIS/
│
├── README.md                           # Master project documentation & architectural handbook
├── .gitignore                          # Root git ignore configuration (Python, Node, secrets, DBs)
│
├── start_all.bat                       # Master batch launcher (Boots FastAPI and Vite concurrently)
├── start_backend.bat                   # Standalone launcher for FastAPI backend
├── start_frontend.bat                  # Standalone launcher for React Vite frontend
│
├── backend/
│   ├── .env                            # Active environment variables (git-ignored)
│   ├── .env.example                    # Template environment variable schema
│   ├── requirements.txt                # Curated Python backend dependencies
│   ├── run.py                          # Uvicorn entry point runner script
│   │
│   ├── app/
│   │   ├── __init__.py                 # Backend application package marker
│   │   ├── main.py                     # FastAPI app factory, CORS, exception handlers, lifespan
│   │   ├── config.py                   # Pydantic BaseSettings and environment variable loader
│   │   ├── database.py                 # SQLAlchemy engine, session maker, Base, init_db, verify
│   │   ├── dependencies.py             # Auth dependency injection (get_current_user)
│   │   │
│   │   ├── models/                     # SQLAlchemy 2.0 ORM database models
│   │   │   ├── __init__.py             # Models package initialization
│   │   │   ├── user.py                 # User account entity model
│   │   │   ├── user_preference.py      # Market & Period preference entity model
│   │   │   ├── saved_stock.py          # Watchlist entity model with unique constraints
│   │   │   └── research_task.py        # ResearchTask and ResearchReport entity models
│   │   │
│   │   ├── routes/                     # FastAPI endpoint route controllers
│   │   │   ├── __init__.py             # Routes package initialization
│   │   │   ├── auth.py                 # /api/auth routes (register, login, logout, me)
│   │   │   ├── preference.py           # /api/preferences routes (GET, PUT)
│   │   │   ├── stocks.py               # /api/stocks routes (search, overview, history)
│   │   │   ├── watchlist.py            # /api/watchlist routes (add, list, delete)
│   │   │   └── research.py             # /api/research routes (tasks, history, task detail)
│   │   │
│   │   ├── schemas/                    # Pydantic v2 data validation schemas
│   │   │   ├── __init__.py             # Schemas package initialization
│   │   │   ├── auth.py                 # Registration and login request/response schemas
│   │   │   ├── preference.py           # Market and period preference schemas
│   │   │   ├── stock.py                # Stock quotes, candles, and validation schemas
│   │   │   ├── watchlist.py            # Watchlist request/response schemas
│   │   │   └── research.py             # Research task and report schemas
│   │   │
│   │   └── services/                   # Business logic and external service layer
│   │       ├── __init__.py             # Services package initialization
│   │       ├── security.py             # Password hashing (bcrypt) and JWT encode/decode
│   │       ├── user_service.py         # User retrieval and registration operations
│   │       ├── preference_service.py   # User market/period preference business logic
│   │       ├── stock_service.py        # yfinance market data fetcher
│   │       ├── validation_service.py   # Market data validation and cleaning rules
│   │       ├── watchlist_service.py    # Saved stocks and watchlist business logic
│   │       └── research_service.py     # Research task execution and history operations
│   │
│   ├── scripts/                        # Maintenance, migration, and live check scripts
│   │   ├── migrations/
│   │   │   └── migrate_task4_schema.py # Safe evolution script for research_reports columns
│   │   │
│   │   └── live_checks/                # Live end-to-end integration test scripts (HTTP)
│   │       ├── verify_all_modules.py   # Full regression test suite across all modules
│   │       ├── verify_compliance_live.py# Schema compliance verifier
│   │       ├── verify_jwt_live.py      # JWT authentication and cookie verification
│   │       ├── verify_task4_live.py    # Research history isolation verification
│   │       └── verify_task5_live.py    # Watchlist CRUD verification
│   │
│   └── tests/                          # Automated Pytest unit & integration test suites
│       ├── __init__.py                 # Tests package marker
│       ├── conftest.py                 # Test fixtures, TestClient setup, and DB overrides
│       ├── test_registration.py        # Task 1 & 2 registration validation tests (7 tests)
│       ├── test_auth_and_stocks.py     # Task 3 login, JWT, and market data tests (5 tests)
│       ├── test_research_history.py    # Task 4 multi-user isolation & report tests (4 tests)
│       ├── test_watchlist.py           # Task 5 watchlist CRUD & duplicate tests (10 tests)
│       └── test_preferences.py         # Task 6 user market/period preferences tests (12 tests)
│
└── frontend/
    ├── .gitignore                      # Frontend build and dependency ignores
    ├── .oxlintrc.json                  # Oxlint configuration rules
    ├── index.html                      # HTML document root template
    ├── package.json                    # NPM packages, dependencies, and build scripts
    ├── package-lock.json               # Locked dependency tree
    ├── postcss.config.js               # PostCSS configuration for Tailwind processing
    ├── tailwind.config.js              # Custom dark crimson design system tokens
    ├── vite.config.js                  # Vite bundler configuration & /api reverse proxy
    │
    ├── public/
    │   └── favicon.svg                 # Stock-market-inspired candlestick logo icon
    │
    └── src/
        ├── App.jsx                     # Root application routing component
        ├── main.jsx                    # React 19 entry point and DOM mounting
        ├── index.css                   # Global styles & Tailwind CSS base directives
        │
        ├── components/
        │   ├── auth/
        │   │   └── RegistrationForm.jsx# Full registration form with password strength bar
        │   ├── research/
        │   │   └── ReportModal.jsx     # Detailed research report modal viewer
        │   ├── ui/
        │   │   ├── AlertBanner.jsx     # Alert banner (error, success, info, warning)
        │   │   ├── InputField.jsx      # Accessible form input field with error messaging
        │   │   ├── PasswordStrengthBar.jsx # Visual multi-segment password entropy meter
        │   │   └── Spinner.jsx         # Accessible loading spinner
        │   └── watchlist/
        │       └── WatchlistSection.jsx# Watchlist grid, item cards, and removal buttons
        │
        ├── hooks/
        │   └── useRegistrationForm.js  # Controlled form hook with real-time validation
        └── pages/
            ├── DashboardPage.jsx       # Primary research workspace & analytics console
            ├── LoginPage.jsx           # Sign in interface with financial chart decoration
            └── RegisterPage.jsx        # Account registration interface
```

---

### 6.2 File-by-File Technical Directory

#### 1. Root-Level Files
- **[README.md](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/README.md)**: Master architectural handbook, technical documentation, and setup guide.
- **[.gitignore](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/.gitignore)**: Comprehensive exclusion file covering Python virtual environments (`venv/`), bytecode (`__pycache__/`), pytest caches, Node modules (`node_modules/`), Vite build distributions (`dist/`), local database files (`*.db`), log files, and environment variable files (`.env`).
- **[start_all.bat](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/start_all.bat)**: Double-click Windows batch script that spawns both the FastAPI backend server (on port 8000) and Vite frontend server (on port 5173) in dedicated terminal windows.
- **[start_backend.bat](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/start_backend.bat)**: Standalone batch script activating `venv` and executing `python backend/run.py`.
- **[start_frontend.bat](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/start_frontend.bat)**: Standalone batch script navigating to `frontend/` and executing `npm run dev`.

#### 2. Backend Application Files
- **[backend/run.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/run.py)**: Standalone entry point that resolves the backend import path and launches Uvicorn with auto-reload.
- **[backend/app/main.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/main.py)**: FastAPI application factory. Registers CORS middleware, global exception handlers for `StarletteHTTPException` and `RequestValidationError`, defines application lifespan (verifying database connectivity on startup), and mounts all five API routers.
- **[backend/app/config.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/config.py)**: Configuration singleton based on Pydantic `BaseSettings`. Loads variables from `backend/.env` with fallback defaults for ports, database URLs, CORS origins, cookie security flags, and JWT settings.
- **[backend/app/database.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/database.py)**: Database abstraction module. Initializes the SQLAlchemy engine with `pool_pre_ping=True`, exports `SessionLocal`, provides the `get_db` generator dependency, `verify_connection()` for diagnostic health checks, and `init_db()` for automatic table creation.
- **[backend/app/dependencies.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/dependencies.py)**: Security dependency injection provider. Defines `get_token_from_request` (extracting JWT from cookie or Bearer header) and `get_current_user` (validating token cryptographic signature and retrieving the active `User` model from PostgreSQL).

#### 3. Backend Database Models
- **[backend/app/models/user.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/models/user.py)**: Maps the `users` table (`user_id`, `full_name`, `email`, `password_hash`, `created_at`). Defines cascade relationships to `saved_stocks`, `research_tasks`, and `preferences`.
- **[backend/app/models/user_preference.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/models/user_preference.py)**: Maps `user_preferences` (`preference_id`, `user_id`, `market`, `analysis_period`, `updated_at`). Enforces a 1-to-1 unique relationship with `users`.
- **[backend/app/models/saved_stock.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/models/saved_stock.py)**: Maps `saved_stocks` (`saved_stock_id`, `user_id`, `ticker`, `created_at`). Declares `UniqueConstraint('user_id', 'ticker')` to prevent duplicate watchlist items per user.
- **[backend/app/models/research_task.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/models/research_task.py)**: Defines `ResearchTask` (`task_id`, `user_id`, `ticker`, `company_name`, `market`, `requested_period`, `status`, `created_at`, `completed_at`) and `ResearchReport` (`report_id`, `task_id`, `report_content`, `overview_data`, `history_data`, `summary`, `limitations`, `created_at`).

#### 4. Backend Route Controllers
- **[backend/app/routes/auth.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/routes/auth.py)**: Implements `/api/auth/register`, `/api/auth/login`, `/api/auth/me`, and `/api/auth/logout`.
- **[backend/app/routes/preference.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/routes/preference.py)**: Implements `GET /api/preferences` and `PUT /api/preferences`. Protected by `get_current_user`.
- **[backend/app/routes/stocks.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/routes/stocks.py)**: Implements `GET /api/stocks/search`, `GET /api/stocks/{ticker}/overview`, and `GET /api/stocks/{ticker}/history`.
- **[backend/app/routes/watchlist.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/routes/watchlist.py)**: Implements `POST /api/watchlist`, `GET /api/watchlist`, and `DELETE /api/watchlist/{saved_stock_id}`.
- **[backend/app/routes/research.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/routes/research.py)**: Implements `POST /api/research/tasks`, `GET /api/research/history`, and `GET /api/research/tasks/{task_id}`.

#### 5. Backend Schemas (Pydantic v2)
- **[backend/app/schemas/auth.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/schemas/auth.py)**: Schemas for registration, login, and profile output.
- **[backend/app/schemas/preference.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/schemas/preference.py)**: Schemas validating allowed markets (`NSE`, `BSE`, `NASDAQ`, `NYSE`) and allowed periods (`1mo`, `3mo`, `6mo`, `1y`, `5y`).
- **[backend/app/schemas/stock.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/schemas/stock.py)**: Schemas for stock search results, fundamental overviews, and OHLCV candlestick records.
- **[backend/app/schemas/watchlist.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/schemas/watchlist.py)**: Schemas for watchlist creation and enriched items.
- **[backend/app/schemas/research.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/schemas/research.py)**: Schemas for research task creation, history listings, reports, and task details.

#### 6. Backend Services Layer
- **[backend/app/services/security.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/security.py)**: Cryptographic functions (`hash_password`, `verify_password`, `create_access_token`, `decode_access_token`, `generate_csrf_token`).
- **[backend/app/services/user_service.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/user_service.py)**: Database interactions for user registration, duplicate email verification, and authentication.
- **[backend/app/services/preference_service.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/preference_service.py)**: Manages retrieval, default creation, and updates for `UserPreference`.
- **[backend/app/services/stock_service.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/stock_service.py)**: Upstream market data retrieval using `yfinance`. Contains a predefined universe of top Indian equities and dynamic ticker lookup.
- **[backend/app/services/validation_service.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/validation_service.py)**: Validates ticker symbols, sanitizes market data, detects zero-volume anomalies, and constructs data quality reports.
- **[backend/app/services/watchlist_service.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/watchlist_service.py)**: Watchlist CRUD operations, duplicate detection, ticker normalization, and metadata resolution.
- **[backend/app/services/research_service.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/research_service.py)**: Orchestrates the research task lifecycle (`Pending` -> `Processing` -> `Completed`/`Failed`), market-ticker validation, and persistence of `ResearchReport` rows.

#### 7. Backend Scripts and Migrations
- **[backend/scripts/migrations/migrate_task4_schema.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/scripts/migrations/migrate_task4_schema.py)**: Safe database evolution script ensuring `report_content` (JSON) and `limitations` (TEXT) exist on `research_reports` while preserving existing records.
- **[backend/scripts/live_checks/verify_all_modules.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/scripts/live_checks/verify_all_modules.py)**: Live end-to-end integration test exercising all six Module 1 endpoints against a running server.
- **[backend/scripts/live_checks/verify_compliance_live.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/scripts/live_checks/verify_compliance_live.py)**: Verifies live database schema compliance for Task 4.
- **[backend/scripts/live_checks/verify_jwt_live.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/scripts/live_checks/verify_jwt_live.py)**: Verifies JWT issuance, HTTP-only cookie receipt, and protected route access.
- **[backend/scripts/live_checks/verify_task4_live.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/scripts/live_checks/verify_task4_live.py)**: Verifies multi-user research history isolation across distinct accounts.
- **[backend/scripts/live_checks/verify_task5_live.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/scripts/live_checks/verify_task5_live.py)**: Verifies live watchlist addition, duplicate prevention, and deletion.

#### 8. Backend Test Suite (Pytest)
- **[backend/tests/conftest.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/tests/conftest.py)**: Defines Pytest fixtures: creates a fresh SQLite in-memory test database, overrides the `get_db` FastAPI dependency, and yields a `TestClient`.
- **[backend/tests/test_registration.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/tests/test_registration.py)**: 7 automated tests verifying user registration success, camelCase compatibility, duplicate email rejection, password mismatch, invalid email format, and weak password rules.
- **[backend/tests/test_auth_and_stocks.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/tests/test_auth_and_stocks.py)**: 5 automated tests verifying registration-to-login workflows, unauthenticated request rejection, invalid token rejection, expired token rejection, and nonexistent user token rejection.
- **[backend/tests/test_research_history.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/tests/test_research_history.py)**: 4 automated tests verifying research task creation, user history isolation, unauthenticated access rejection, and recording of failed tasks.
- **[backend/tests/test_watchlist.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/tests/test_watchlist.py)**: 10 automated tests verifying stock saving, 409 duplicate rejection, ticker normalization, cross-user same-ticker saving, isolation, deletion, cross-user deletion prevention, 404 handling, and unauthenticated rejection.
- **[backend/tests/test_preferences.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/tests/test_preferences.py)**: 12 automated tests verifying preference retrieval, default initialization (`NSE`, `1mo`), updates for market and period, validation of disallowed options (422), unauthenticated rejection, cross-user preference isolation, cross-user modification prevention, and research workflow parameter compatibility.

#### 9. Frontend Configuration Files
- **[frontend/package.json](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/package.json)**: Declares dependencies (React 19, Lucide React, Tailwind CSS) and scripts (`dev`, `build`, `lint`, `preview`).
- **[frontend/vite.config.js](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/vite.config.js)**: Configures the Vite development server with proxying: routes `/api/*` requests to `http://127.0.0.1:8000` with `changeOrigin: true`.
- **[frontend/tailwind.config.js](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/tailwind.config.js)**: Defines design system tokens: rich black background (`#060608`), card dark charcoal (`#0c0c12`), crimson accent palette (`#e11d48`, `#be123c`), and font styling.
- **[frontend/postcss.config.js](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/postcss.config.js)**: Configures PostCSS plugins (`tailwindcss`, `autoprefixer`).
- **[frontend/.oxlintrc.json](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/.oxlintrc.json)**: Linter configuration ensuring high-quality React code standards.

#### 10. Frontend Components
- **[frontend/src/components/auth/RegistrationForm.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/components/auth/RegistrationForm.jsx)**: Controlled form component for account registration. Includes visibility toggles, client-side validation, password entropy indicator, and accessibility attributes.
- **[frontend/src/components/research/ReportModal.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/components/research/ReportModal.jsx)**: Accessible modal dialog displaying deep financial reports. Fetches `/api/research/tasks/{task_id}` and renders company overview metrics, analytical summaries, and system limitations.
- **[frontend/src/components/watchlist/WatchlistSection.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/components/watchlist/WatchlistSection.jsx)**: Renders the saved stocks card grid, displaying live price quotes, percentage changes, company names, 1-click research initiation buttons, and deletion triggers.
- **[frontend/src/components/ui/AlertBanner.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/components/ui/AlertBanner.jsx)**: Reusable notification component supporting `error`, `success`, `info`, and `warning` variants.
- **[frontend/src/components/ui/InputField.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/components/ui/InputField.jsx)**: Accessible input field wrapper with label, validation styling, error messages, and right-hand accessory slot.
- **[frontend/src/components/ui/PasswordStrengthBar.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/components/ui/PasswordStrengthBar.jsx)**: Multi-segment visual bar indicating password entropy score (Weak, Fair, Good, Strong).
- **[frontend/src/components/ui/Spinner.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/components/ui/Spinner.jsx)**: SVG loading animation component supporting multiple sizes.

#### 11. Frontend Hooks
- **[frontend/src/hooks/useRegistrationForm.js](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/hooks/useRegistrationForm.js)**: Custom hook encapsulating registration form state, touch tracking, real-time validation logic, and asynchronous submission to `/api/auth/register`.

#### 12. Frontend Pages
- **[frontend/src/pages/RegisterPage.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/pages/RegisterPage.jsx)**: Full-page view hosting the registration card, brand logo, value proposition bullet points, and navigation link to `/login`.
- **[frontend/src/pages/LoginPage.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/pages/LoginPage.jsx)**: Full-page view hosting the login card, financial chart line backdrop, credential submission, and authentication state transitions.
- **[frontend/src/pages/DashboardPage.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/pages/DashboardPage.jsx)**: Master workspace. Contains the persistent sidebar, top navigation bar, stock search and period controller, Bento KPI grid with SVG sparklines, interactive chart, dual research history and watchlist panels, and expandable OHLCV table.

#### 13. Frontend Styles and Assets
- **[frontend/src/index.css](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/index.css)**: Global CSS file defining Tailwind `@tailwind base`, `@tailwind components`, `@tailwind utilities`, custom scrollbars, and selection highlights.
- **[frontend/public/favicon.svg](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/public/favicon.svg)**: Scalable vector icon depicting financial candlesticks in the crimson design palette.

---

## 7. Backend Architecture — Deep Technical Explanation

### 7.1 Core Subsystems

#### FastAPI Initialization and Lifespan Management
The application is created via `FastAPI()` in [app/main.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/main.py). It registers an `@asynccontextmanager` lifespan handler. On startup, the lifespan invokes `init_db()`, which binds all models to the engine, ensures required database columns exist via safe schema inspection, and verifies database responsiveness via `verify_connection()`.

#### Configuration Management
The configuration system in [app/config.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/config.py) utilizes `pydantic-settings.BaseSettings`. Configuration values are read from `backend/.env` (or environment variables). The system parses comma-separated `CORS_ORIGINS` into Python lists and configures cookie names, token expiration times, and database connection strings.

#### Database Session Lifecycle and Connection Pooling
Connections are managed by SQLAlchemy 2.0 in [app/database.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/database.py):
- `pool_pre_ping=True`: Tests connections prior to handing them to requests, transparently reconnecting stale connections.
- `get_db()`: Implements a Python generator yielding a fresh `SessionLocal` instance per HTTP request and cleanly closing the session in a `finally` block upon request completion.

#### Cross-Origin Resource Sharing (CORS) Policy
Configured in `main.py` using `CORSMiddleware`:
- `allow_origins`: Loaded from `settings.cors_origins_list` (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`).
- `allow_origin_regex`: `^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$` allows dynamic local development ports.
- `allow_credentials=True`: Permits browser inclusion of cookies and authorization headers across origins.
- `allow_methods=["*"]`, `allow_headers=["*"]`.

#### Global Exception Handling
- `StarletteHTTPException`: Catches all HTTP exceptions (400, 401, 403, 404, 409, 500) and formats them into a uniform JSON response: `{ "status": "error", "status_code": int, "detail": str, "path": str }`.
- `RequestValidationError`: Catches Pydantic schema validation failures (HTTP 422) and serializes error details into structured JSON.

---

### 7.2 Master API Routes Registry

| HTTP Method | Route Path | Purpose | Authentication | Request Payload | Response Schema |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Root API status verification | None | None | `{ message: str, docs: str }` |
| `GET` | `/api/health` | Health and database connectivity check | None | None | `{ status: str, database: dict }` |
| `POST` | `/api/auth/register` | Register a new user account | None | `UserRegisterRequest` | `RegisterSuccessResponse` (201) |
| `POST` | `/api/auth/login` | Authenticate user and issue JWT cookie | None | `UserLoginRequest` | `LoginSuccessResponse` (200) |
| `GET` | `/api/auth/me` | Retrieve authenticated profile | Required | None | `CurrentUserResponse` (200) |
| `POST` | `/api/auth/logout` | Terminate session and clear cookies | None | None | `LogoutSuccessResponse` (200) |
| `GET` | `/api/preferences` | Retrieve user market & period preferences | Required | None | `PreferenceResponse` (200) |
| `PUT` | `/api/preferences` | Update user market & period preferences | Required | `PreferenceUpdate` | `PreferenceResponse` (200) |
| `GET` | `/api/stocks/search` | Search tickers by query symbol/name | Required | Query param `q` (min 1 char) | `StockSearchResponse` (200) |
| `GET` | `/api/stocks/{ticker}/overview` | Retrieve fundamental overview | Required | Path param `ticker` | `StockOverviewResponse` (200) |
| `GET` | `/api/stocks/{ticker}/history` | Retrieve historical OHLCV candles | Required | Path `ticker`, Query `period` | `HistoricalDataResponse` (200) |
| `GET` | `/api/watchlist` | Retrieve user's saved stocks | Required | None | `WatchlistResponse` (200) |
| `POST` | `/api/watchlist` | Save stock ticker to watchlist | Required | `SavedStockCreate` | `SavedStockResponse` (201) |
| `DELETE` | `/api/watchlist/{saved_stock_id}`| Remove saved stock from watchlist | Required | Path param `saved_stock_id` | `{ status: str, message: str }` (200) |
| `POST` | `/api/research/tasks` | Create and execute research task | Required | `ResearchTaskCreate` | `ResearchTaskDetailResponse` (201) |
| `GET` | `/api/research/history` | List user's research execution history | Required | None | `ResearchHistoryResponse` (200) |
| `GET` | `/api/research/tasks/{task_id}` | Retrieve research task details & report | Required | Path param `task_id` | `ResearchTaskDetailResponse` (200) |

---

## 8. Frontend Architecture — Deep Technical Explanation

### 8.1 Single-Page Application Design

#### Root Mount and Client Routing
The frontend entry point is [frontend/src/main.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/main.jsx), which renders `<App />` into the DOM `#root` container. [frontend/src/App.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/App.jsx) establishes client-side navigation using React Router DOM (`BrowserRouter`).

#### Route Definitions
- `/`: Redirects immediately to `/register`.
- `/register`: Renders `RegisterPage`.
- `/login`: Renders `LoginPage`.
- `/dashboard`: Renders `DashboardPage`.
- `*`: Fallback route redirecting all unknown URLs to `/login`.

#### Route Protection Pattern
Route protection is enforced within `DashboardPage.jsx` via an initial `useEffect` hook. When `/dashboard` mounts:
1. Dispatches an asynchronous fetch to `/api/auth/me` with `credentials: 'include'`.
2. If the response status is not 200 OK (token missing or expired), it purges `localStorage.removeItem('currentUser')` and triggers `navigate('/login', { state: { message: 'Authentication required. Please sign in to continue.' } })`.
3. If valid, it stores user metadata in React component state.

---

### 8.2 UI Components and Presentation Layer

#### Dashboard Architecture ([DashboardPage.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/pages/DashboardPage.jsx))
1. **Persistent Sidebar**: Contains the official brand logo (`SAI ANALYSIS`), active tab indicators (`Workspace`, `Research Engine`, `Portfolio Analytics`), service health badges, and user profile pill with 1-click logout.
2. **Top Navigation Bar**: Displays dynamic greetings, live system clock, engine status pill, notification bell, and primary research execution trigger.
3. **Stock Lookup Controller**: Features a debounced search input (300ms debounce), market dropdown (`NSE`, `BSE`, `NASDAQ`, `NYSE`), duration selector (`1mo`, `3mo`, `6mo`, `1y`, `5y`), and dynamic autocomplete popup.
4. **Bento KPI Grid**: 4-card metric display presenting Current Price, 24h Change, 52-Week Range, and Market Capitalization, each rendered with custom embedded SVG sparklines.
5. **Interactive Stock Performance Chart**: Responsive SVG chart displaying historical price curves, linear gradients, date markers, and volume bar graphs.
6. **Dual Research Workspace**:
   - **Left Panel (Research Activity History)**: Displays previous analytical tasks, ticker badges, market and period tags, execution statuses (`Completed`, `Failed`, `Processing`), and a report viewer modal trigger.
   - **Right Panel (Watchlist & Saved Stocks)**: Powered by `WatchlistSection.jsx`, enabling rapid tracking, live quote inspection, 1-click cross-workspace research, and item removal.
7. **Expandable OHLCV Data Table**: Collapsible table displaying verified candlestick records (Date, Open, High, Low, Close, Volume).

---

## 9. Database Architecture

### 9.1 Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    users ||--o{ saved_stocks : "owns (1:N, cascade delete)"
    users ||--o{ research_tasks : "initiates (1:N, cascade delete)"
    users ||--o| user_preferences : "configures (1:1, cascade delete)"
    research_tasks ||--o| research_reports : "generates (1:1, cascade delete)"

    users {
        int user_id PK "autoincrement"
        varchar(100) full_name "NOT NULL"
        varchar(255) email "NOT NULL, UNIQUE, index"
        varchar(255) password_hash "NOT NULL"
        datetime created_at "NOT NULL, default now()"
    }

    user_preferences {
        int preference_id PK "autoincrement"
        int user_id FK "NOT NULL, UNIQUE, index, users.user_id ON DELETE CASCADE"
        varchar(20) market "NOT NULL, default 'NSE'"
        varchar(20) analysis_period "NOT NULL, default '1mo'"
        datetime updated_at "NOT NULL, default now()"
    }

    saved_stocks {
        int saved_stock_id PK "autoincrement"
        int user_id FK "NOT NULL, index, users.user_id ON DELETE CASCADE"
        varchar(20) ticker "NOT NULL, index"
        datetime created_at "NOT NULL, default now()"
    }

    research_tasks {
        int task_id PK "autoincrement"
        int user_id FK "NOT NULL, index, users.user_id ON DELETE CASCADE"
        varchar(20) ticker "NOT NULL, index"
        varchar(255) company_name "NOT NULL"
        varchar(50) market "NOT NULL, default 'NSE'"
        varchar(20) requested_period "NOT NULL, default '1mo'"
        varchar(20) status "NOT NULL, index, default 'Pending'"
        datetime created_at "NOT NULL, default now()"
        datetime completed_at "NULL"
    }

    research_reports {
        int report_id PK "autoincrement"
        int task_id FK "NOT NULL, UNIQUE, index, research_tasks.task_id ON DELETE CASCADE"
        json report_content "NULL"
        json overview_data "NOT NULL"
        json history_data "NOT NULL"
        text summary "NULL"
        text limitations "NULL"
        datetime created_at "NOT NULL, default now()"
    }
```

---

### 9.2 Table Specifications and Schemas

#### 1. `users` Table
Stores authenticated user accounts.
- `user_id` (INTEGER, Primary Key, autoincrement): Unique identifier.
- `full_name` (VARCHAR(100), NOT NULL): User's legal or display name.
- `email` (VARCHAR(255), NOT NULL, UNIQUE, Indexed): Normalized lowercase email address.
- `password_hash` (VARCHAR(255), NOT NULL): 12-round bcrypt hash string (`$2b$12$...`).
- `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL): Account creation timestamp.

#### 2. `user_preferences` Table
Stores personalized workspace defaults for each user.
- `preference_id` (INTEGER, Primary Key, autoincrement): Unique identifier.
- `user_id` (INTEGER, NOT NULL, UNIQUE, Indexed): Foreign key referencing `users.user_id` with `ON DELETE CASCADE`.
- `market` (VARCHAR(20), NOT NULL, default `'NSE'`): Preferred market (`NSE`, `BSE`, `NASDAQ`, `NYSE`).
- `analysis_period` (VARCHAR(20), NOT NULL, default `'1mo'`): Preferred duration (`1mo`, `3mo`, `6mo`, `1y`, `5y`).
- `updated_at` (TIMESTAMP WITH TIME ZONE, NOT NULL): Last modification timestamp.

#### 3. `saved_stocks` Table
Stores stocks saved to user watchlists.
- `saved_stock_id` (INTEGER, Primary Key, autoincrement): Unique identifier.
- `user_id` (INTEGER, NOT NULL, Indexed): Foreign key referencing `users.user_id` with `ON DELETE CASCADE`.
- `ticker` (VARCHAR(20), NOT NULL, Indexed): Stock symbol (e.g., `INFY.NS`, `AAPL`).
- `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL): Creation timestamp.
- **Constraints**: `UniqueConstraint('user_id', 'ticker', name='uq_user_saved_ticker')` prevents duplicate tickers per user.

#### 4. `research_tasks` Table
Records analytical task executions.
- `task_id` (INTEGER, Primary Key, autoincrement): Unique identifier.
- `user_id` (INTEGER, NOT NULL, Indexed): Foreign key referencing `users.user_id` with `ON DELETE CASCADE`.
- `ticker` (VARCHAR(20), NOT NULL, Indexed): Stock symbol researched.
- `company_name` (VARCHAR(255), NOT NULL): Company name resolved from market metadata.
- `market` (VARCHAR(50), NOT NULL, default `'NSE'`): Market under which research occurred.
- `requested_period` (VARCHAR(20), NOT NULL, default `'1mo'`): Horizon requested.
- `status` (VARCHAR(20), NOT NULL, Indexed, default `'Pending'`): Lifecycle state (`Pending`, `Processing`, `Completed`, `Failed`).
- `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL): Initiation timestamp.
- `completed_at` (TIMESTAMP WITH TIME ZONE, NULLABLE): Termination timestamp.

#### 5. `research_reports` Table
Stores persistent financial research reports generated by tasks.
- `report_id` (INTEGER, Primary Key, autoincrement): Unique identifier.
- `task_id` (INTEGER, NOT NULL, UNIQUE, Indexed): Foreign key referencing `research_tasks.task_id` with `ON DELETE CASCADE`.
- `report_content` (JSON, NULLABLE): Master structured analytical report document.
- `overview_data` (JSON, NOT NULL): Fundamental snapshot (P/E, Market Cap, 52W Range, etc.).
- `history_data` (JSON, NOT NULL): Array of validated OHLCV candlestick objects.
- `summary` (TEXT, NULLABLE): Analytical narrative.
- `limitations` (TEXT, NULLABLE): Disclaimer documenting data source limitations.
- `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL): Report generation timestamp.

---

### 9.3 Safe Database Inspection Queries

To verify database contents without modifying data or risking integrity loss:

```sql
-- 1. Verify all tables in public schema
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 2. Inspect record counts across tables
SELECT 
    (SELECT COUNT(*) FROM users) AS total_users,
    (SELECT COUNT(*) FROM user_preferences) AS total_preferences,
    (SELECT COUNT(*) FROM saved_stocks) AS total_saved_stocks,
    (SELECT COUNT(*) FROM research_tasks) AS total_research_tasks,
    (SELECT COUNT(*) FROM research_reports) AS total_research_reports;

-- 3. Verify user isolation across watchlists
SELECT u.email, COUNT(s.saved_stock_id) AS watchlist_count
FROM users u
LEFT JOIN saved_stocks s ON u.user_id = s.user_id
GROUP BY u.user_id, u.email;

-- 4. Verify research task state distribution
SELECT status, COUNT(*) AS count
FROM research_tasks
GROUP BY status;
```

---

## 10. Complete Application Workflows

### Workflow A: User Registration
1. **Starting Point**: User navigates to `/register`.
2. **User Action**: Enters Full Name, Email, Password, and Confirm Password; clicks "Create Account".
3. **Frontend File**: [RegistrationForm.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/components/auth/RegistrationForm.jsx) and [useRegistrationForm.js](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/hooks/useRegistrationForm.js).
4. **API Endpoint**: `POST /api/auth/register`.
5. **Backend Route File**: [backend/app/routes/auth.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/routes/auth.py).
6. **Service Logic**: [register_new_user](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/user_service.py) checks email uniqueness, runs `hash_password()`.
7. **Database Table**: Inserts into `users`.
8. **Response**: HTTP 201 Created with `RegisterSuccessResponse`.
9. **Final UI Result**: Green alert banner displayed; redirects to `/login`.
10. **Error Scenarios**: Email already registered returns HTTP 409 Conflict. Password mismatch or weak format returns HTTP 400 Bad Request.

### Workflow B: User Authentication and Login
1. **Starting Point**: User navigates to `/login`.
2. **User Action**: Enters email and password; clicks "Sign In".
3. **Frontend File**: [LoginPage.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/pages/LoginPage.jsx).
4. **API Endpoint**: `POST /api/auth/login`.
5. **Backend Route File**: [backend/app/routes/auth.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/routes/auth.py).
6. **Service Logic**: [authenticate_user](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/user_service.py) verifies password via `verify_password()`; generates token via `create_access_token()`.
7. **Database Table**: Queries `users`.
8. **Response**: HTTP 200 OK + `Set-Cookie: access_token=...; HttpOnly; SameSite=lax`.
9. **Final UI Result**: Sets `localStorage('currentUser')`; navigates to `/dashboard`.
10. **Error Scenarios**: Invalid password or unknown email returns HTTP 401 Unauthorized. Server down displays network error alert.

### Workflow C: Protected Workspace Access
1. **Starting Point**: User opens or refreshes `/dashboard`.
2. **User Action**: Direct browser navigation or route transition.
3. **Frontend File**: [DashboardPage.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/pages/DashboardPage.jsx).
4. **API Endpoint**: `GET /api/auth/me`.
5. **Backend Route File**: [backend/app/routes/auth.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/routes/auth.py).
6. **Service Logic**: [get_current_user](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/dependencies.py) decodes JWT from cookie; checks database for user.
7. **Database Table**: Queries `users`.
8. **Response**: HTTP 200 OK with `CurrentUserResponse`.
9. **Final UI Result**: Dashboard initializes research history, preferences, and watchlist.
10. **Error Scenarios**: Missing or expired cookie returns HTTP 401; user redirected to `/login`.

### Workflow D: User Logout
1. **Starting Point**: User clicks "Sign Out" in dashboard sidebar.
2. **User Action**: Clicks logout button.
3. **Frontend File**: [DashboardPage.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/pages/DashboardPage.jsx).
4. **API Endpoint**: `POST /api/auth/logout`.
5. **Backend Route File**: [backend/app/routes/auth.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/routes/auth.py).
6. **Service Logic**: Deletes `access_token` and `csrf_token` cookies.
7. **Database Table**: No database write required.
8. **Response**: HTTP 200 OK with `LogoutSuccessResponse`.
9. **Final UI Result**: Clears `localStorage`; redirects to `/login`.
10. **Error Scenarios**: Subsequent attempts to access `/dashboard` fail with HTTP 401.

### Workflow E: Research Task Execution and History
1. **Starting Point**: User selects ticker and period in dashboard search bar.
2. **User Action**: Clicks "Run Research" or selects quick ticker.
3. **Frontend File**: [DashboardPage.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/pages/DashboardPage.jsx).
4. **API Endpoint**: `POST /api/research/tasks`.
5. **Backend Route File**: [backend/app/routes/research.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/routes/research.py).
6. **Service Logic**: [execute_research_workflow](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/research_service.py) creates task (`Pending`), transitions to `Processing`, fetches market data via `yfinance`, generates `ResearchReport`, updates task to `Completed`.
7. **Database Table**: Inserts into `research_tasks` and `research_reports`.
8. **Response**: HTTP 201 Created with `ResearchTaskDetailResponse`.
9. **Final UI Result**: Bento KPIs update, SVG chart plots historical data, research history list refreshes.
10. **Error Scenarios**: Incompatible market/ticker raises HTTP 400. Upstream data failure records task as `Failed`.

### Workflow F: Stock Watchlist Management
1. **Starting Point**: User views stock in search bar or overview panel.
2. **User Action**: Clicks "Save to Watchlist" or clicks the remove trash icon.
3. **Frontend File**: [DashboardPage.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/pages/DashboardPage.jsx) and [WatchlistSection.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/components/watchlist/WatchlistSection.jsx).
4. **API Endpoint**: `POST /api/watchlist` (Add) or `DELETE /api/watchlist/{saved_stock_id}` (Remove).
5. **Backend Route File**: [backend/app/routes/watchlist.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/routes/watchlist.py).
6. **Service Logic**: [watchlist_service.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/watchlist_service.py) validates ticker, verifies duplicate status, manages database row.
7. **Database Table**: Modifies `saved_stocks`.
8. **Response**: HTTP 201 Created (Add) or HTTP 200 OK (Delete).
9. **Final UI Result**: Watchlist card grid re-renders immediately.
10. **Error Scenarios**: Adding an existing ticker returns HTTP 409 Conflict. Deleting an item belonging to another user returns HTTP 404/403.

### Workflow G: User Market and Period Preferences
1. **Starting Point**: User changes Market (`NSE`, `BSE`, `NASDAQ`, `NYSE`) or Period (`1mo`, `3mo`, `6mo`, `1y`, `5y`) dropdowns in the dashboard.
2. **User Action**: Clicks "Save Preferences".
3. **Frontend File**: [DashboardPage.jsx](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/frontend/src/pages/DashboardPage.jsx).
4. **API Endpoint**: `PUT /api/preferences`.
5. **Backend Route File**: [backend/app/routes/preference.py](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/routes/preference.py).
6. **Service Logic**: [update_user_preference](file:///c:/Users/vadla/Desktop/INTERNSHIP_INFO/AI-Powered%20Multi%20Agent%20System%20for%20Market%20Analysis%20and%20Research%20(1)/backend/app/services/preference_service.py) validates options and updates the database row.
7. **Database Table**: Updates `user_preferences`.
8. **Response**: HTTP 200 OK with `PreferenceResponse`.
9. **Final UI Result**: Green confirmation alert displayed; subsequent research operations inherit saved settings.
10. **Error Scenarios**: Submitting unsupported values returns HTTP 422 Unprocessable Content.

---

## 11. API Documentation

### Interactive Swagger and ReDoc Exploration
FastAPI automatically generates interactive OpenAPI documentation:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

#### How to Authorize in Swagger UI
1. Execute `POST /api/auth/login` in Swagger with valid credentials.
2. Copy the returned `access_token` string from the JSON response.
3. Click the **Authorize** button at the top right of the Swagger UI page.
4. In the `HTTPBearer` dialog, paste the token and click **Authorize**.
5. All subsequent requests in Swagger will supply `Authorization: Bearer <token>`.

---

### Detailed Endpoint Specifications

#### 1. POST `/api/auth/register`
- **Description**: Registers a new user account.
- **Authentication**: None.
- **Request Body**:
  ```json
  {
    "fullName": "Jane Doe",
    "email": "jane.doe@example.com",
    "password": "SecurePassword123!",
    "confirmPassword": "SecurePassword123!"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "status": "success",
    "message": "User registered successfully.",
    "data": {
      "user_id": 1,
      "email": "jane.doe@example.com",
      "full_name": "Jane Doe",
      "role": "Analyst",
      "created_at": "2026-11-16T08:30:00Z"
    }
  }
  ```

#### 2. POST `/api/auth/login`
- **Description**: Authenticates user credentials and issues an HTTP-only JWT cookie.
- **Authentication**: None.
- **Request Body**:
  ```json
  {
    "email": "jane.doe@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "Login successful.",
    "data": {
      "user_id": 1,
      "email": "jane.doe@example.com",
      "full_name": "Jane Doe",
      "role": "Analyst",
      "created_at": "2026-11-16T08:30:00Z"
    }
  }
  ```

#### 3. GET `/api/preferences`
- **Description**: Retrieves caller's preferences (initializes defaults if new user).
- **Authentication**: Required (`access_token`).
- **Response (200 OK)**:
  ```json
  {
    "preference_id": 1,
    "user_id": 1,
    "market": "NSE",
    "analysis_period": "1mo",
    "updated_at": "2026-11-16T08:30:00Z"
  }
  ```

#### 4. PUT `/api/preferences`
- **Description**: Updates market and analysis period preferences.
- **Authentication**: Required.
- **Request Body**:
  ```json
  {
    "market": "NASDAQ",
    "analysis_period": "1y"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "preference_id": 1,
    "user_id": 1,
    "market": "NASDAQ",
    "analysis_period": "1y",
    "updated_at": "2026-11-16T08:35:00Z"
  }
  ```

#### 5. POST `/api/watchlist`
- **Description**: Saves a ticker to the authenticated user's watchlist.
- **Authentication**: Required.
- **Request Body**:
  ```json
  {
    "ticker": "INFY.NS"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "saved_stock_id": 1,
    "user_id": 1,
    "ticker": "INFY.NS",
    "company_name": "Infosys Limited",
    "exchange": "NSE",
    "created_at": "2026-11-16T08:35:00Z"
  }
  ```

#### 6. DELETE `/api/watchlist/{saved_stock_id}`
- **Description**: Removes a saved stock from the user's watchlist.
- **Authentication**: Required.
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "Stock 'INFY.NS' successfully removed from watchlist."
  }
  ```

#### 7. POST `/api/research/tasks`
- **Description**: Initiates and executes an asynchronous stock research workflow.
- **Authentication**: Required.
- **Request Body**:
  ```json
  {
    "ticker": "INFY.NS",
    "market": "NSE",
    "period": "1mo"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "status": "success",
    "task": {
      "task_id": 101,
      "user_id": 1,
      "ticker": "INFY.NS",
      "company_name": "Infosys Limited",
      "market": "NSE",
      "requested_period": "1mo",
      "status": "Completed",
      "has_report": true,
      "created_at": "2026-11-16T08:40:00Z",
      "completed_at": "2026-11-16T08:40:02Z"
    },
    "report": {
      "report_id": 55,
      "task_id": 101,
      "overview_data": {
        "ticker": "INFY.NS",
        "company_name": "Infosys Limited",
        "current_price": 1850.5,
        "market_cap": 768000000000
      },
      "history_data": [
        {
          "timestamp": "2026-11-14T00:00:00Z",
          "open": 1845.0,
          "high": 1860.0,
          "low": 1840.0,
          "close": 1850.5,
          "volume": 4500000
        }
      ],
      "summary": "Infosys exhibits steady operational momentum...",
      "limitations": "Data retrieved via yfinance market data service for INFY.NS.",
      "created_at": "2026-11-16T08:40:02Z"
    }
  }
  ```

---

## 12. Environment Setup

### Prerequisites
- **Operating System**: Windows 11 (or Windows 10, macOS, Linux).
- **Python**: Version 3.10, 3.11, or 3.12 (Verify via `python --version`).
- **Node.js**: Version 18.x or 20.x with `npm` (Verify via `node -v` and `npm -v`).
- **PostgreSQL**: Version 14 or higher running on `localhost:5432`.

---

### Step-by-Step Installation Guide (Windows 11)

#### Step 1: Open Terminal in Project Root
Launch PowerShell or Windows Terminal and navigate to the project directory:
```powershell
cd "c:\Users\vadla\Desktop\INTERNSHIP_INFO\AI-Powered Multi Agent System for Market Analysis and Research (1)"
```

#### Step 2: Virtual Environment Setup
Check if `venv` exists. If not, create and activate it:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Step 3: Install Backend Dependencies
Install all required packages from `backend/requirements.txt`:
```powershell
pip install -r backend\requirements.txt
```

#### Step 4: Install Frontend Dependencies
Navigate to the `frontend` folder and install dependencies:
```powershell
cd frontend
npm install
cd ..
```

#### Step 5: Configure Environment File
Ensure `backend/.env` exists. If missing, copy from template:
```powershell
Copy-Item backend\.env.example backend\.env
```
Open `backend/.env` and verify your PostgreSQL credentials:
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/stock_research_db
JWT_SECRET_KEY=replace_with_a_secure_random_32_byte_secret_key
```

#### Step 6: Verify Database Existence
Ensure PostgreSQL is running and database `stock_research_db` is created. Using `psql`:
```powershell
psql -U postgres -c "CREATE DATABASE stock_research_db;"
```

#### Step 7: Verify Database Connectivity
Test backend connectivity using Python:
```powershell
.\venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend'); from app.database import verify_connection; print(verify_connection())"
```

---

## 13. Environment Variables and Configuration

| Variable Name | Purpose | Required | Example Format | Default Value |
| :--- | :--- | :--- | :--- | :--- |
| `APP_NAME` | Name displayed in logs and documentation | No | `"SAI ANALYSIS"` | `"Multi-Agent Stock Research Analyst"` |
| `APP_ENV` | Runtime environment flag | No | `development` / `production` | `development` |
| `DEBUG` | Enables hot reloading and stack traces | No | `True` / `False` | `True` |
| `PORT` | FastAPI backend port | No | `8000` | `8000` |
| `HOST` | Backend bind host IP | No | `127.0.0.1` | `127.0.0.1` |
| `DATABASE_URL` | PostgreSQL connection string | **Yes** | `postgresql://USER:PASSWORD@HOST:PORT/DBNAME` | Localhost template |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | No | `http://localhost:5173,http://localhost:3000` | `http://localhost:5173,...` |
| `JWT_SECRET_KEY` | Secret key for signing HMAC-SHA256 tokens | **Yes** | 32+ character random string | Development placeholder |
| `JWT_ALGORITHM` | Cryptographic JWT algorithm | No | `HS256` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration duration in minutes | No | `60` | `60` |
| `AUTH_COOKIE_NAME`| Name of HTTP-only authentication cookie | No | `access_token` | `access_token` |
| `COOKIE_SECURE` | Enforces HTTPS requirement for cookies | **Yes in Prod** | `False` (Dev) / `True` (Prod) | `False` |
| `COOKIE_SAMESITE`| SameSite cookie CSRF policy | No | `lax` / `strict` | `lax` |

---

## 14. Running the Project

### Option A: Master One-Click Startup (Recommended)
From the project root, run:
```cmd
start_all.bat
```
Spawns both the FastAPI backend and Vite frontend development servers in separate console windows.

---

### Option B: Dedicated Terminal Startup

#### Terminal 1 — FastAPI Backend Server
```powershell
# Working Directory: Project Root
.\venv\Scripts\Activate.ps1
python backend\run.py
```
- **Expected Console Output**:
  ```text
  Starting Multi-Agent Stock Research Analyst on http://127.0.0.1:8000
  Interactive Swagger Documentation: http://127.0.0.1:8000/docs
  INFO:     Started server process
  INFO:     Waiting for application startup.
  INFO:uvicorn.error:Initializing database connection and schema...
  INFO:uvicorn.error:Database connected successfully (postgresql://localhost:5432/stock_research_db)
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
  ```

#### Terminal 2 — React Vite Frontend Server
```powershell
# Working Directory: frontend/
cd frontend
npm run dev
```
- **Expected Console Output**:
  ```text
  VITE v8.3.7  ready in 240 ms
  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
  ```

---

### Stopping the Development Servers
In each respective terminal window, press `Ctrl + C` and confirm termination by typing `Y`.

---

## 15. Testing and Quality Assurance

### Automated Pytest Suite
The backend contains 38 automated unit and integration tests verifying all six Module 1 requirements.

#### Run Complete Test Suite
```powershell
# Working Directory: Project Root
.\venv\Scripts\pytest.exe backend\tests\ -v
```

#### Run Individual Test Modules
```powershell
# Test user registration validation rules
.\venv\Scripts\pytest.exe backend\tests\test_registration.py -v

# Test authentication, JWT issuance, and market overview
.\venv\Scripts\pytest.exe backend\tests\test_auth_and_stocks.py -v

# Test research history creation and cross-user isolation
.\venv\Scripts\pytest.exe backend\tests\test_research_history.py -v

# Test watchlist CRUD, uniqueness constraints, and isolation
.\venv\Scripts\pytest.exe backend\tests\test_watchlist.py -v

# Test user preferences defaults, validation, and persistence
.\venv\Scripts\pytest.exe backend\tests\test_preferences.py -v
```

---

### Frontend Static Analysis and Build Checks

#### Run Frontend Linting (Oxlint)
```powershell
# Working Directory: frontend/
npm run lint
```
*Expected Result: 0 errors.*

#### Run Production Build
```powershell
# Working Directory: frontend/
npm run build
```
*Expected Result: Transforms 2,000+ modules and produces optimized bundle in `dist/` with 0 errors.*

---

### Live Integration Checks
With the backend running on `http://127.0.0.1:8000`:
```powershell
# Run full live integration verification
.\venv\Scripts\python.exe backend\scripts\live_checks\verify_all_modules.py

# Verify live JWT authentication cookies
.\venv\Scripts\python.exe backend\scripts\live_checks\verify_jwt_live.py

# Verify live watchlist operations
.\venv\Scripts\python.exe backend\scripts\live_checks\verify_task5_live.py
```

---

## 16. Manual Testing Guide

| Test Scenario | Action / Input | Expected Result |
| :--- | :--- | :--- |
| **1. New Registration** | Register new email with valid 8+ character password containing 1 uppercase and 1 number. | Registration succeeds; green alert banner displayed; redirects to `/login`. |
| **2. Duplicate Registration** | Attempt to register with the same email address. | Registration rejected with HTTP 409 Conflict; alert shows "Email already in use". |
| **3. Password Mismatch** | Enter different values in Password and Confirm Password fields. | Client-side error displayed immediately; submission button remains disabled. |
| **4. Valid Login** | Submit registered email and valid password. | Authentication succeeds; HTTP-only cookie set; redirects to `/dashboard`. |
| **5. Invalid Login** | Submit unregistered email or incorrect password. | Authentication rejected with HTTP 401; generic error message displayed. |
| **6. Dashboard Handshake** | Refresh `/dashboard` while authenticated. | Handshake against `/api/auth/me` succeeds; workspace loads user preferences. |
| **7. Protected Access** | Clear cookies and attempt to navigate to `/dashboard`. | Handshake fails; user immediately redirected to `/login` with warning alert. |
| **8. Preference Update** | Select `NASDAQ` and `1y`; click "Save Preferences". | Green confirmation alert appears; preferences persist across page reloads. |
| **9. Watchlist Add** | Search `INFY.NS`; click "Save to Watchlist". | Stock appears in right-hand watchlist card grid with live price quote. |
| **10. Watchlist Duplicate** | Attempt to save `INFY.NS` again. | Blocked with HTTP 409 Conflict; alert displays duplicate warning. |
| **11. Watchlist Remove** | Click trash can icon on saved stock card. | Stock removed from database and immediately excised from the UI card grid. |
| **12. Research Execution** | Search `TCS.NS` and click "Run Research". | Bento KPIs update, SVG performance chart renders, research history updates. |
| **13. Report Modal** | Click a completed task in the history panel. | Modal overlay opens displaying fundamental ratios, summary, and limitations. |
| **14. User Isolation** | Log in as User B and inspect history and watchlist. | User B sees zero records from User A. All data is strictly user-isolated. |
| **15. User Logout** | Click "Sign Out" in the sidebar. | Session terminated; cookies cleared; user redirected to `/login`. |

---

## 17. Error Handling and Troubleshooting

### 1. Backend Fails to Start: `ModuleNotFoundError: No module named 'app'`
- **Cause**: Python path does not include the `backend/` directory.
- **Solution**: Execute commands from the repository root using `python backend/run.py` or set `$env:PYTHONPATH="backend"` in PowerShell.

### 2. Port Conflict: `OSError: [Errno 10048] address already in use: 8000`
- **Cause**: Another instance of Uvicorn or another application is using port 8000.
- **Troubleshooting**:
  ```powershell
  # Identify process on port 8000
  netstat -ano | findstr :8000
  # Terminate process by PID
  taskkill /PID <PID_NUMBER> /F
  ```

### 3. Port Conflict: `Port 5173 is in use`
- **Cause**: Another Vite development server is running.
- **Solution**: Terminate the existing node process or allow Vite to use fallback port `5174` (note: ensure CORS origins include `http://localhost:5174`).

### 4. PostgreSQL Connection Failure: `OperationalError: connection to server at "localhost"`
- **Cause**: PostgreSQL service is stopped, port 5432 is blocked, or credentials in `backend/.env` are incorrect.
- **Troubleshooting**:
  ```powershell
  # Check PostgreSQL Windows Service
  Get-Service -Name postgresql*
  # Start PostgreSQL Service if stopped
  Start-Service postgresql*
  ```
  Verify `DATABASE_URL` username, password, host, and database name in `backend/.env`.

### 5. Authentication Cookie Not Stored by Browser
- **Cause**: Frontend origin does not match backend CORS policy or `credentials: 'include'` is omitted in `fetch`.
- **Solution**: Ensure requests supply `{ credentials: 'include' }`. Verify that `backend/app/config.py` includes your client port in `CORS_ORIGINS`.

---

## 18. Security Implementation

### Cryptographic Security Measures
- **Bcrypt Password Encryption**: User passwords are encrypted with `bcrypt` using 12 salt rounds. Passwords are never stored in plaintext.
- **HMAC-SHA256 Token Signing**: JWT access tokens are signed using a 256-bit secret key, validating token integrity and expiration.
- **HTTP-Only Cookie Defense**: Session cookies are configured with `HttpOnly=True`, preventing client-side JavaScript access via `document.cookie` and mitigating token extraction via Cross-Site Scripting (XSS).
- **SameSite Protection**: Cookies declare `SameSite=lax` to protect against Cross-Site Request Forgery (CSRF).
- **SQL Injection Prevention**: All database interactions use SQLAlchemy ORM parameterized queries. Raw string formatting of user input is prohibited.
- **Input Validation**: Pydantic v2 schemas validate input types, lengths, email syntax, and allowed values before business logic executes.
- **Multi-Tenant Data Isolation**: Database queries enforce user ownership filtering (`user_id = current_user.user_id`).

### Production Security Considerations
Before deploying to production:
1. Generate a cryptographically secure `JWT_SECRET_KEY` (e.g., `openssl rand -hex 32`).
2. Set `COOKIE_SECURE=True` in `backend/.env` to require HTTPS transmission.
3. Configure `DEBUG=False` in `backend/.env` to suppress debug traces.
4. Restrict `CORS_ORIGINS` strictly to production domain names.

---

## 19. Current Implementation Status

| Milestone Requirement | Description | Implementation Status | Relevant Files | Verification Method |
| :--- | :--- | :--- | :--- | :--- |
| **Task 1: User Interface** | Responsive crimson/pitch-black layout, auth views | **Fully Implemented** | `DashboardPage.jsx`, `LoginPage.jsx`, `RegisterPage.jsx` | Visual inspection, clean build |
| **Task 2: Registration** | Form validation, bcrypt hashing, unique email | **Fully Implemented** | `auth.py`, `user_service.py`, `RegistrationForm.jsx` | Automated tests (7/7 passed) |
| **Task 3: Authentication** | Login, JWT cookies, session guard, logout | **Fully Implemented** | `auth.py`, `security.py`, `dependencies.py` | Automated tests (5/5 passed) |
| **Task 4: Research History** | Multi-user research tasks, reports, modal viewer | **Fully Implemented** | `research.py`, `research_service.py`, `ReportModal.jsx` | Automated tests (4/4 passed) |
| **Task 5: Stock Watchlist** | Autocomplete search, add/remove stock, isolation | **Fully Implemented** | `watchlist.py`, `watchlist_service.py`, `WatchlistSection.jsx` | Automated tests (10/10 passed) |
| **Task 6: Preferences** | Market and period options, defaults, persistence | **Fully Implemented** | `preference.py`, `preference_service.py`, `user_preference.py`| Automated tests (12/12 passed) |

---

## 20. Known Limitations

1. **Market Data Provider Rate Limits**: Upstream market data retrieval uses `yfinance`. Excessive rapid requests may be subject to rate limiting by Yahoo Finance servers.
2. **Exchange Ticker Suffixes**: Indian equities require explicit exchange suffixes (`.NS` for NSE, `.BO` for BSE) for external market lookups. The platform automatically normalizes top predefined equities, but non-indexed symbols require correct suffix formatting.
3. **Historical Trading Days**: In historical data analysis, holidays and weekend days produce gaps in calendar timelines. Candle validation filters zero-volume days while documenting sample counts in report limitations.
4. **Local Development Cookie Setting**: By default, `COOKIE_SECURE` is set to `False` to facilitate local testing over unencrypted HTTP. Must be enabled for HTTPS environments.

---

## 21. Future Enhancements

The following capabilities represent future development milestones (Modules 2 through 4):
- **Autonomous Multi-Agent Analysis (Module 2)**: Integrating LangGraph/CrewAI worker agents for automated fundamental, technical, sentiment, and risk analysis.
- **Automated Report Export**: Generation of downloadable PDF and CSV research summaries from completed analytical tasks.
- **Technical Indicators Engine**: Native calculation of RSI, MACD, Bollinger Bands, and Moving Averages directly within backend services.
- **WebSocket Price Streaming**: Real-time push updates for active watchlist tickers using WebSockets.

---

## 22. Developer Maintenance Guide

### How to Add a New Backend API Route
1. Define request and response schemas in `backend/app/schemas/`.
2. Implement business logic functions in `backend/app/services/`.
3. Create endpoint handlers in `backend/app/routes/`, declaring `Depends(get_current_user)` if authentication is required.
4. Register the router in `backend/app/main.py` via `app.include_router()`.
5. Add corresponding automated unit tests in `backend/tests/`.

### How to Add a Database Model
1. Create a model class in `backend/app/models/` inheriting from `Base` (imported from `app.database`).
2. Define fields, foreign keys with `ondelete='CASCADE'`, unique constraints, and indexes.
3. Import the new model class in `backend/app/models/__init__.py`.
4. `init_db()` in `app/database.py` will automatically create the table on next startup.

### How to Add a Frontend Component
1. Create a new JSX component file in `frontend/src/components/`.
2. Style the component using Tailwind CSS utility classes adhering to the black (`#060608`) and crimson (`#e11d48`) design tokens.
3. Use Lucide React for vector icons (`import { IconName } from 'lucide-react'`).
4. Ensure components handle loading, error, and empty states gracefully.

---

## 23. Important Commands Reference

| Operation | Directory | Command |
| :--- | :--- | :--- |
| **Run All Servers** | Project Root | `.\start_all.bat` |
| **Activate Virtual Environment** | Project Root | `.\venv\Scripts\Activate.ps1` |
| **Start Backend Manually** | Project Root | `.\venv\Scripts\python.exe backend\run.py` |
| **Start Frontend Manually** | `frontend/` | `npm run dev` |
| **Run All Pytest Tests** | Project Root | `.\venv\Scripts\pytest.exe backend\tests\ -v` |
| **Run Specific Test File** | Project Root | `.\venv\Scripts\pytest.exe backend\tests\test_preferences.py -v` |
| **Run Frontend Linter** | `frontend/` | `npm run lint` |
| **Build Frontend Bundle** | `frontend/` | `npm run build` |
| **Run Schema Migration** | Project Root | `.\venv\Scripts\python.exe backend\scripts\migrations\migrate_task4_schema.py` |
| **Run Live System Check** | Project Root | `.\venv\Scripts\python.exe backend\scripts\live_checks\verify_all_modules.py` |

---

## 24. Project Completion Summary

**SAI ANALYSIS: Multi-Agent Stock Research Analyst** represents a clean, fully verified implementation of Module 1:
- **Architecture**: Modular, decoupled client-server architecture with strict separation of concerns across models, schemas, services, and presentation.
- **Security**: Complete authentication lifecycle utilizing bcrypt hashing, HMAC-SHA256 JWTs, HTTP-only SameSite cookies, and route protection.
- **Relational Integrity**: Complete PostgreSQL relational schema enforcing unique constraints, foreign-key cascade deletions, and multi-tenant data isolation.
- **Quality Assurance**: 38 out of 38 automated tests passing, clean frontend build with zero compilation errors, and comprehensive live verification scripts.

*The codebase is structurally sound, clean, maintainable, and prepared for Module 2 agentic extensions.*
