# FinCrew — Autonomous Multi-Agent Equity Research Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20SQLAlchemy%202.x-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![TailwindCSS](https://img.shields.io/badge/Styling-Tailwind%20CSS%203.4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

FinCrew is a full-stack, autonomous multi-agent equity research desk that synthesizes institutional-grade investment memorandums for public equities. By orchestrating a pipeline of five specialist analytical agents—Market Research, Financial Valuation, Technical Signals, Sentiment Catalysts, and Risk Severity—FinCrew aggregates live financial telemetry, performs quantitative modeling, resolves adversarial risk constraints, and synthesizes committee-level consensus dossiers.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Proposed Solution](#3-proposed-solution)
4. [Key Features](#4-key-features)
5. [Five AI Specialist Agents](#5-five-ai-specialist-agents)
6. [Multi-Agent Orchestration Workflow](#6-multi-agent-orchestration-workflow)
7. [Technology Stack](#7-technology-stack)
8. [System Architecture](#8-system-architecture)
9. [Project Directory Structure](#9-project-directory-structure)
10. [Major Backend Files and Responsibilities](#10-major-backend-files-and-responsibilities)
11. [Major Frontend Files and Responsibilities](#11-major-frontend-files-and-responsibilities)
12. [Database Models and Schema Relationships](#12-database-models-and-schema-relationships)
13. [API Endpoints Reference](#13-api-endpoints-reference)
14. [Authentication and Security Architecture](#14-authentication-and-security-architecture)
15. [Installation Prerequisites](#15-installation-prerequisites)
16. [macOS Setup Instructions](#16-macos-setup-instructions)
17. [Windows Setup Instructions](#17-windows-setup-instructions)
18. [PostgreSQL Database Configuration](#18-postgresql-database-configuration)
19. [Environment Variable Configuration](#19-environment-variable-configuration)
20. [Backend Dependency Installation](#20-backend-dependency-installation)
21. [Frontend Dependency Installation](#21-frontend-dependency-installation)
22. [Running the Backend Server](#22-running-the-backend-server)
23. [Running the Frontend Client](#23-running-the-frontend-client)
24. [Interactive Swagger API Documentation](#24-interactive-swagger-api-documentation)
25. [Application User Guide](#25-application-user-guide)
26. [Five-Agent Analysis Lifecycle](#26-five-agent-analysis-lifecycle)
27. [Multi-Format Document Exports (PDF, JSON, HTML, Markdown)](#27-multi-format-document-exports-pdf-json-html-markdown)
28. [Automated Testing Suite](#28-automated-testing-suite)
29. [Troubleshooting & FAQ](#29-troubleshooting--faq)
30. [Current Limitations & Future Enhancements](#30-current-limitations--future-enhancements)

---

## 1. Project Overview

FinCrew is engineered as an institutional equity analysis engine. Rather than relying on single-prompt language models prone to hallucinations and unverified numbers, FinCrew applies specialized analytical agents to live financial telemetry. The platform manages the entire lifecycle of investment analysis: from raw data retrieval via upstream market feeds, to deterministic technical and fundamental factor modeling, lexical sentiment analysis of earnings and news headlines, adversarial bear-case stress testing, and committee consensus synthesis.

Completed research sessions are permanently archived in PostgreSQL with complete user data isolation, supporting multi-stock comparative matrices and instantaneous exports in PDF, JSON, HTML, and Markdown formats.

---

## 2. Problem Statement

Retail investors, portfolio managers, and equity analysts face significant hurdles when conducting thorough equity due diligence:
- **Information Fragmentation**: Balance sheet filings, valuation multiples, price action charts, news flow, and risk factors are scattered across disparate paywalled portals.
- **Superficial AI Outputs**: Generic LLM queries produce generic prose, hallucinate outdated market prices, or fail to cross-validate balance sheet solvency against debt obligations.
- **Confirmation Bias**: Traditional single-analyst workflows frequently overlook downside tail risks, margin contraction pressures, or debt rollover risks during bullish momentum cycles.
- **Manual Synthesis Overhead**: Consolidating findings into presentation-ready memos, datasets, and executive briefs requires hours of repetitive document formatting.

---

## 3. Proposed Solution

FinCrew solves these inefficiencies through an autonomous multi-agent architecture:
- **Specialized Division of Labor**: Five discrete agents independently evaluate market positioning, valuation ratios, chart oscillators, media tone, and downside vulnerabilities.
- **Adversarial Synthesis**: The Risk Severity Agent acts as a dedicated devil's advocate, directly counterbalancing optimistic assumptions before a committee rating is formulated.
- **Mathematical Consistency**: Calculated target prices, implied upside percentages, and valuation multiples are derived from real market data feeds without data fabrication.
- **Enterprise-Grade Architecture**: Built on a decoupled FastAPI and React stack backed by PostgreSQL, featuring strict JWT token lifecycle management, thread-safe memory caching, and multi-format document generators.

---

## 4. Key Features

- **Autonomous Research Pipeline**: Single-click multi-agent dispatch on any US equity ticker (e.g. `AAPL`, `MSFT`, `NVDA`, `GOOGL`, `AMZN`, `TSLA`).
- **Interactive Executive Dashboard**: Real-time KPI summaries, dynamic Sector Exposure distribution, animated month timeline navigation, and custom date range filters.
- **Adversarial Risk Modeling**: Quantitative stress testing of volatility (beta), drawdown potential, leverage risk, and bear-case downside price targets.
- **Side-by-Side Multi-Stock Comparison**: Comparative evaluation across 2 to 5 concurrent research sessions with multi-agent factor matrices and normalized return rankings.
- **Multi-Format Export Engine**: Production generation of Executive PDF reports, structured JSON datasets, standalone responsive HTML dossiers, and GitHub-flavored Markdown.
- **Complete User Isolation**: Multi-tenant database design ensuring users only view, compare, export, and delete their own research sessions.
- **Thread-Safe In-Memory Cache**: TTL-based cache preventing upstream rate-limit throttling during rapid re-queries.

---

## 5. Five AI Specialist Agents

```
                           ┌───────────────────────────────┐
                           │      Upstream Market Data     │
                           │   (yfinance + Market Cache)   │
                           └───────────────┬───────────────┘
                                           │
         ┌───────────────────┬─────────────┴───────┬───────────────────┐
         ▼                   ▼                     ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Market Research │ │    Financial    │ │    Technical    │ │    Sentiment    │
│    Specialist   │ │ Valuation Agent │ │  Signals Agent  │ │ Catalysts Agent │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                     │                   │
         └───────────────────┴─────────────┬───────┴───────────────────┘
                                           ▼
                               ┌───────────────────────┐
                               │     Risk Severity     │
                               │   (Adversary / CRO)   │
                               └───────────┬───────────┘
                                           ▼
                               ┌───────────────────────┐
                               │     CIO Consensus     │
                               │ Synthesis Orchestrator│
                               └───────────────────────┘
```

### 1. Market Research Specialist (`MarketResearchAgent`)
- **Domain**: Macroeconomic environment, company profile, and competitive moat.
- **Responsibilities**:
  - Classifies market capitalization tiers: Mega-Cap ($200B+), Large-Cap ($10B-$200B), Mid-Cap ($2B-$10B), Small-Cap (<$2B).
  - Determines sector and industry taxonomy according to standard GICS groupings.
  - Synthesizes core revenue drivers, operating segments, and business model fundamentals.

### 2. Financial Valuation Analyst (`FinancialAnalysisAgent`)
- **Domain**: Fundamental accounting metrics, financial ratios, and intrinsic valuation.
- **Responsibilities**:
  - Evaluates valuation multiples: Trailing P/E, Forward P/E, EV/EBITDA, Price-to-Book (P/B), and Price-to-Sales (P/S).
  - Analyzes profitability margins: Gross margin, operating margin, net profit margin, and Return on Equity (ROE).
  - Computes solvency ratios: Debt-to-Equity, Total Debt, Total Cash, and Operating/Free Cash Flow health.
  - Assigns fundamental valuation status: `UNDERVALUED`, `FAIRLY_VALUED`, or `OVERVALUED`.

### 3. Technical Signals Specialist (`TechnicalAnalysisAgent`)
- **Domain**: Quantitative price action, moving averages, momentum, and technical setup.
- **Responsibilities**:
  - Computes 14-period Relative Strength Index (RSI-14) to flag oversold (<30) or overbought (>70) conditions.
  - Evaluates trend structure against the 50-day and 200-day Simple Moving Averages (Golden Cross / Death Cross).
  - Identifies dynamic support and resistance channels using 52-week trading ranges and average true volatility bands.
  - Formulates technical outlook: `BULLISH`, `NEUTRAL`, or `BEARISH`.

### 4. Sentiment & Catalysts Analyst (`SentimentAnalysisAgent`)
- **Domain**: Financial news flow, regulatory press releases, and earnings commentary.
- **Responsibilities**:
  - Implements a domain-specific financial lexical scoring engine with weighted positive and negative keyword lexicons.
  - Parses real-time news headlines to identify imminent catalysts (product launches, earnings beats, strategic partnerships).
  - Identifies negative headwinds (litigation, regulatory scrutiny, guidance cuts).
  - Outputs normalized sentiment score (-1.0 to +1.0) and categorical stance: `BULLISH`, `NEUTRAL`, or `BEARISH`.

### 5. Risk Severity & Downside Analyst (`RiskAnalysisAgent`)
- **Domain**: Adversarial stress testing, downside tail risks, and capital preservation.
- **Responsibilities**:
  - Acts as Chief Risk Officer (CRO) to independently stress-test the assumptions of the other four agents.
  - Evaluates market sensitivity (beta), maximum drawdown potential, and interest coverage safety.
  - Models bear-case downside price targets based on valuation compression and support retests.
  - Assigns quantitative risk score (1.0 to 10.0) and classification: `LOW`, `MODERATE`, `HIGH`, or `CRITICAL`.

---

## 6. Multi-Agent Orchestration Workflow

The orchestration pipeline is executed deterministically by `ResearchOrchestrator`:

1. **Market Data Acquisition**: Raw telemetry (quote, overview, balance sheet, financial ratios, news headlines, historical price bars) is retrieved through `MarketDataService` with cache interception.
2. **Specialist Agent Execution**: The 5 analytical agents run sequentially against the structured data payload, producing strongly typed Pydantic output schemas.
3. **Multi-Factor Committee Scoring**:
   The Chief Investment Officer (CIO) algorithm applies multi-factor weights to synthesize individual agent outputs:
   $$\text{Composite Score} = (0.35 \times \text{Valuation}) + (0.20 \times \text{Technical}) + (0.20 \times \text{Sentiment}) - (0.25 \times \text{Risk Penalty})$$
4. **Target Price Synthesis**: Computes a mathematically consistent 12-month target price blending fundamental DCF multiples, technical breakout channels, and risk-adjusted bear-case boundaries.
5. **Consensus Recommendation**: Categorizes composite scores into five committee ratings:
   - `STRONG_BUY` (High upside $\ge 15\%$, high confidence, low/moderate risk)
   - `BUY` (Upside between $5\%$ and $15\%$, moderate/high confidence)
   - `HOLD` (Neutral expected returns between $-5\%$ and $+5\%$, or balanced bull/bear forces)
   - `SELL` (Downside risk between $-5\%$ and $-15\%$)
   - `STRONG_SELL` (Downside risk $> -15\%$, critical leverage, or deteriorating fundamentals)
6. **Executive Narrative Compilation**: Synthesizes a structured 5-part investment memorandum and commits the record to PostgreSQL.

---

## 7. Technology Stack

### Backend Stack
- **Language**: Python 3.10+
- **Framework**: FastAPI 0.115+ (Asynchronous ASGI REST API)
- **ASGI Web Server**: Uvicorn 0.30+ (with standard uvloop & websockets workers)
- **Database ORM**: SQLAlchemy 2.0+ (Declarative 2.0 mapped columns and relationships)
- **PostgreSQL Driver**: Psycopg 3.2+ (`psycopg[binary]`)
- **Database Migrations**: Alembic 1.13+
- **Settings Management**: Pydantic Settings 2.4+ (Type-safe `.env` parsing)
- **Security & Cryptography**: Bcrypt 4.0+ (password hashing), PyJWT 2.9+ (HMAC-SHA256 JWT tokens)
- **Market Data Feed**: yfinance 0.2.40+, Pandas 2.2+, NumPy 1.26+
- **Document Generation**: fpdf2 2.8+ (vector PDF document synthesis)
- **Automated Testing**: Pytest 8.0+, HTTPX 0.27+ (TestClient)

### Frontend Stack
- **Framework**: React 18.3+ (Single Page Application with Hooks architecture)
- **Build Tooling & Dev Server**: Vite 6.0+ (Native ESM bundling and Hot Module Replacement)
- **CSS Styling Framework**: Tailwind CSS 3.4+ (Custom FinCrew design system tokens)
- **Icon Suite**: Lucide React 1.16+
- **PostCSS**: Autoprefixer 10.4+, PostCSS 8.4+
- **Browser Automation**: Puppeteer Core 25.17+ (Headless UI verification)

---

## 8. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Client Browser                        │
│                (React 18 + Vite + Tailwind)                 │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON (REST API)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                     │
│  ┌────────────────────┬──────────────────┬───────────────┐  │
│  │    Auth Router     │ Research Router  │ Health Router │  │
│  └─────────┬──────────┴─────────┬────────┴───────┬───────┘  │
│            ▼                    ▼                ▼          │
│  ┌───────────────────┐┌──────────────────────────────────┐  │
│  │ Security & Token  ││      Research Orchestrator       │  │
│  │ Revocation Engine ││  ┌────────────────────────────┐  │  │
│  └───────────────────┘│  │ 5 Specialist Agents (AI)   │  │  │
│                       │  └────────────────────────────┘  │  │
│                       │  ┌────────────────────────────┐  │  │
│                       │  │ Market Data & TTL Cache    │  │  │
│                       │  └────────────────────────────┘  │  │
│                       │  ┌────────────────────────────┐  │  │
│                       │  │ Comparative & Analytics    │  │  │
│                       │  └────────────────────────────┘  │  │
│                       │  ┌────────────────────────────┐  │  │
│                       │  │ PDF / JSON / HTML Exporter │  │  │
│                       │  └────────────────────────────┘  │  │
│                       └─────────────────┬────────────────┘  │
│                                         │                   │
│                                         ▼                   │
│                       ┌──────────────────────────────────┐  │
│                       │      SQLAlchemy 2.0 ORM Base     │  │
│                       └─────────────────┬────────────────┘  │
└─────────────────────────────────────────┼───────────────────┘
                                          │ Psycopg 3 Driver
                                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                     │
│  ┌───────────────┬─────────────────────┬─────────────────┐  │
│  │  users table  │  research_sessions  │ research_reports│  │
│  └───────────────┴─────────────────────┴─────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                 revoked_tokens table                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Project Directory Structure

```text
FinCrew/
├── .env.example                     # Root environment configuration template
├── .gitignore                       # Git ignore rules for Python, Node, OS files
├── README.md                        # Primary project documentation
├── backend/
│   ├── .env.example                 # Backend environment template
│   ├── alembic.ini                  # Alembic database migration configuration
│   ├── requirements.txt             # Direct Python backend dependencies
│   ├── alembic/                     # Database migration revisions and env
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── app/                         # Core FastAPI application package
│   │   ├── __init__.py
│   │   ├── config.py                # Pydantic Settings application configuration
│   │   ├── database.py              # SQLAlchemy 2.0 engine and Session factory
│   │   ├── dependencies.py          # FastAPI dependencies (auth, database)
│   │   ├── main.py                  # FastAPI application entrypoint and middleware
│   │   ├── security.py              # Bcrypt password hashing and JWT encoding/decoding
│   │   ├── models/                  # SQLAlchemy ORM database models
│   │   │   ├── __init__.py
│   │   │   ├── research.py          # ResearchSession and ResearchReport models
│   │   │   ├── revoked_token.py     # RevokedToken blacklisted JWT model
│   │   │   └── user.py              # User account model
│   │   ├── routers/                 # REST API router endpoints
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # Authentication (register, login, me, logout)
│   │   │   ├── health.py            # System and database health probes
│   │   │   └── research.py          # Research sessions, reports, export, compare
│   │   ├── schemas/                 # Pydantic request and response schemas
│   │   │   ├── __init__.py
│   │   │   ├── agent_outputs.py     # Specialist agent typed output schemas
│   │   │   ├── analytics.py         # Workspace summary analytics schema
│   │   │   ├── auth.py              # Auth credentials and token response schemas
│   │   │   ├── comparison.py        # Multi-stock comparison response schemas
│   │   │   ├── market_data.py       # Raw market data telemetry schema
│   │   │   ├── research.py          # Research session and report schemas
│   │   │   └── user.py              # User profile response schema
│   │   └── services/                # Business logic, orchestration, and agents
│   │       ├── __init__.py
│   │       ├── comparative_analysis.py # Multi-stock comparative analysis service
│   │       ├── market_data.py       # Telemetry ingestion and normalization service
│   │       ├── market_data_cache.py # Thread-safe in-memory TTL caching service
│   │       ├── report_exporter.py   # Multi-format (PDF, JSON, HTML, MD) exporter
│   │       ├── research_orchestrator.py # Multi-agent workflow and CIO synthesis
│   │       ├── workspace_analytics.py # Workspace metrics and sector distribution
│   │       └── agents/              # Five specialist analytical agent modules
│   │           ├── __init__.py
│   │           ├── financial_analysis_agent.py
│   │           ├── market_research_agent.py
│   │           ├── risk_analysis_agent.py
│   │           ├── sentiment_analysis_agent.py
│   │           └── technical_analysis_agent.py
│   └── tests/                       # Comprehensive automated testing suite
│       ├── test_agents.py           # Unit tests for individual specialist agents
│       ├── test_auth.py             # Auth, token lifecycle, and user isolation tests
│       ├── test_market_data.py      # Telemetry fetching and parsing tests
│       ├── test_research_api.py     # Research endpoints and validation tests
│       ├── test_research_models.py  # SQLAlchemy cascading CRUD tests
│       ├── test_stage6a_export_and_cache.py # Cache TTL and document export tests
│       └── test_stage6b_compare_and_analytics.py # Multi-stock comparison tests
└── frontend/
    ├── index.html                   # Single-page HTML entry point
    ├── package.json                 # Node.js dependencies and build scripts
    ├── package-lock.json            # Deterministic Node dependency lockfile
    ├── postcss.config.js            # PostCSS configuration for Tailwind
    ├── tailwind.config.js           # Tailwind theme configuration and colors
    ├── vite.config.js               # Vite bundler configuration and proxy
    └── src/
        ├── index.css                # Global CSS stylesheet and typography rules
        ├── main.jsx                 # React root renderer
        ├── App.jsx                  # Main view coordinator and session state
        ├── api/
        │   └── client.js            # Fetch API client with Bearer auth interception
        └── components/              # Institutional UI React components
            ├── AuthLayout.jsx       # Split-pane authentication frame
            ├── CompareView.jsx      # Multi-stock side-by-side comparison view
            ├── DashboardView.jsx    # Investment dashboard and analytics
            ├── ExportModal.jsx      # Multi-format report download dialog
            ├── FinCrewLogo.jsx      # Vector brand logo mark
            ├── HistoryView.jsx      # Research history and archives table
            ├── LoginForm.jsx        # Login interface
            ├── PageHeader.jsx       # Standardized page title header
            ├── RegisterForm.jsx     # User registration interface
            ├── ReportView.jsx       # Comprehensive Consensus Research Report
            ├── ResearchView.jsx     # Stock Equity Research Pipeline
            ├── StockLogo.jsx        # Vector brand logos for tracked equities
            └── TopNav.jsx           # Floating capsule top navigation bar
```

---

## 10. Major Backend Files and Responsibilities

- **`backend/app/main.py`**: Initializes the FastAPI application instance, registers CORS middleware, configures lifespan events, and mounts API routers (`/api/auth`, `/api/research`, `/api/health`).
- **`backend/app/config.py`**: Declares application settings using Pydantic Settings, parsing environment variables from `.env` with strict type validation.
- **`backend/app/database.py`**: Creates the SQLAlchemy 2.0 engine with connection pool pre-pinging and defines the scoped `get_db()` request dependency.
- **`backend/app/security.py`**: Contains cryptographic utilities for Bcrypt password hashing (`hash_password`, `verify_password`), SHA-256 token indexing (`hash_token`), and JWT generation/decoding (`create_access_token`, `decode_access_token`).
- **`backend/app/dependencies.py`**: FastAPI dependency injector verifying Bearer JWTs, enforcing database revocation checks, and delivering the authenticated `User` record.
- **`backend/app/services/research_orchestrator.py`**: Core orchestration engine coordinating market data ingestion, five specialist agent executions, CIO consensus calculation, and database persistence.
- **`backend/app/services/market_data.py`**: Normalizes upstream financial data from yfinance into strongly validated Pydantic structures.
- **`backend/app/services/market_data_cache.py`**: Implements thread-safe in-memory caching with TTL expiration to safeguard against IP rate limiting.
- **`backend/app/services/report_exporter.py`**: Renders completed research reports into binary PDF memorandums, formatted JSON payloads, sanitized HTML files, and Markdown documents.
- **`backend/app/services/comparative_analysis.py`**: Performs multi-stock peer comparisons across 2 to 5 equities, aligning metrics side-by-side without data fabrication.
- **`backend/app/services/workspace_analytics.py`**: Computes portfolio analytics, status distributions, confidence averages, and sector exposure percentages.
- **`backend/app/services/agents/*.py`**: Discrete modular implementations of the 5 specialist AI agents.

---

## 11. Major Frontend Files and Responsibilities

- **`frontend/src/App.jsx`**: Central view coordinator managing JWT tokens in `localStorage`, tracking user profile state, handling logout events, and routing between Dashboard, Research, Report, History, and Comparison views.
- **`frontend/src/api/client.js`**: Reusable Fetch API abstraction automatically attaching JWT Bearer tokens, intercepting 401 Unauthorized responses to trigger session expiration events, and managing binary blob downloads.
- **`frontend/src/components/TopNav.jsx`**: Capsule top navigation bar featuring active tab indicators, quick action triggers, user avatar, and session termination.
- **`frontend/src/components/DashboardView.jsx`**: Primary dashboard containing 4 KPI metrics, Sector Exposure progress bars, animated Month Timeline navigation, custom date range filtering, and a dark Recent Research Reports panel with list/grid toggle.
- **`frontend/src/components/ResearchView.jsx`**: Pipeline initiating stock research, ticker input with search normalization, quick-pick equity badges, and real-time status across the 5 agent workflow cards.
- **`frontend/src/components/ReportView.jsx`**: Comprehensive consensus report interface with current market price, target price, implied return potential, tabbed specialist breakdowns, and export triggers.
- **`frontend/src/components/HistoryView.jsx`**: Archival table listing historical research sessions with filtering, ticker search, report viewing, export triggers, and session deletion.
- **`frontend/src/components/CompareView.jsx`**: Comparative analysis interface comparing 2 to 5 completed equities with metric matrix tables and normalized performance rankings.
- **`frontend/src/components/ExportModal.jsx`**: Clean modal interface allowing one-click downloads of PDF, JSON, HTML, and Markdown reports.
- **`frontend/src/components/StockLogo.jsx`**: Official SVG vector brand marks for Apple (`AAPL`), NVIDIA (`NVDA`), Amazon (`AMZN`), Microsoft (`MSFT`), Google (`GOOGL`), and Tesla (`TSLA`).

---

## 12. Database Models and Schema Relationships

```
┌──────────────────────┐               ┌───────────────────────────┐
│        users         │               │     research_sessions     │
├──────────────────────┤               ├───────────────────────────┤
│ id (PK, Integer)     │◄─────────────┐│ id (PK, Integer)          │
│ email (UQ, String)   │              └┤ user_id (FK -> users.id)  │
│ hashed_password (Str)│               │ ticker (String)           │
│ full_name (String)   │               │ company_name (String)     │
│ created_at (DateTime)│               │ status (String)           │
│ updated_at (DateTime)│               │ error_message (Text)      │
└──────────┬───────────┘               │ created_at (DateTime)     │
           │                           │ completed_at (DateTime)   │
           │                           └─────────────┬─────────────┘
           │                                         │
           ▼                                         ▼ 1-to-1
┌──────────────────────┐               ┌───────────────────────────┐
│    revoked_tokens    │               │     research_reports      │
├──────────────────────┤               ├───────────────────────────┤
│ id (PK, Integer)     │               │ id (PK, Integer)          │
│ jti (UQ, String)     │               │ session_id (FK, Unique)   │
│ token_hash (UQ, Str) │               │ ticker (String)           │
│ user_id (FK -> users)│               │ company_name (String)     │
│ revoked_at (DateTime)│               │ current_price (Float)     │
│ expires_at (DateTime)│               │ target_price (Float)      │
└──────────────────────┘               │ recommendation (String)   │
                                       │ confidence_score (Float)  │
                                       │ executive_summary (Text)  │
                                       │ fundamental_data (JSON)   │
                                       │ technical_data (JSON)     │
                                       │ sentiment_data (JSON)     │
                                       │ risk_data (JSON)          │
                                       │ created_at (DateTime)     │
                                       └───────────────────────────┘
```

---

## 13. API Endpoints Reference

### Authentication Endpoints (`/api/auth`)
| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register a new user account with bcrypt password hashing | Public |
| `POST` | `/api/auth/login` | Authenticate credentials and receive a signed JWT access token | Public |
| `GET` | `/api/auth/me` | Fetch authenticated user profile details | Bearer JWT |
| `POST` | `/api/auth/logout` | Revoke current access token in PostgreSQL | Bearer JWT |

### Research & Analysis Endpoints (`/api/research`)
| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/research/analyze` | Synchronous end-to-end execution of the 5-agent pipeline | Bearer JWT |
| `POST` | `/api/research/sessions` | Create a pending research session record | Bearer JWT |
| `POST` | `/api/research/sessions/{id}/start` | Trigger asynchronous pipeline execution on a session | Bearer JWT |
| `GET` | `/api/research/sessions` | List user research sessions with pagination | Bearer JWT |
| `GET` | `/api/research/sessions/{id}` | Retrieve session status, timestamps, and error details | Bearer JWT |
| `GET` | `/api/research/sessions/{id}/report`| Retrieve synthesized consensus report and specialist data | Bearer JWT |
| `GET` | `/api/research/sessions/{id}/export`| Export report in `pdf`, `json`, `html`, or `markdown` format | Bearer JWT |
| `DELETE`| `/api/research/sessions/{id}` | Delete research session and cascade-delete report | Bearer JWT |
| `POST` | `/api/research/compare` | Compare 2 to 5 completed sessions side-by-side | Bearer JWT |
| `GET` | `/api/research/analytics/summary` | Fetch workspace KPI metrics and sector allocations | Bearer JWT |

### System Health Endpoints (`/api/health`)
| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Basic application process health probe | Public |
| `GET` | `/api/db-health` | PostgreSQL database connection probe | Public |

---

## 14. Authentication and Security Architecture

- **Password Hashing**: Plaintext passwords are salt-hashed using **Bcrypt** with 12 computational rounds. The standard Bcrypt 72-byte truncation boundary is safely validated before processing.
- **Signed JWT Tokens**: Authentication tokens are signed using the HMAC-SHA256 (`HS256`) algorithm with an expiration duration (default: 60 minutes).
- **Cryptographic Token Revocation**: Logging out records a SHA-256 hash of the token along with its unique `jti` in the `revoked_tokens` table. Every authenticated request verifies against this table to reject revoked tokens immediately.
- **User Isolation**: All research queries, comparisons, analytics summaries, and export actions enforce user ID filtering at the database layer (`WHERE user_id = current_user.id`).
- **Input Sanitization**: Tickers are validated using regex (`^[A-Za-z0-9\.\-]{1,10}$`) and converted to uppercase. HTML exports sanitize external strings to protect against XSS injection.

---

## 15. Installation Prerequisites

Ensure the following tools are installed on your host machine:
- **Python**: Version `3.10`, `3.11`, or `3.12` (Python 3.10+ required)
- **Node.js**: Version `18.0.0` or later (LTS recommended)
- **npm**: Version `9.0.0` or later
- **PostgreSQL**: Version `14` or later (Postgres.app, Homebrew, or Docker)
- **Git**: For version control management

---

## 16. macOS Setup Instructions

```bash
# 1. Clone repository
git clone https://github.com/your-username/FinCrew.git
cd FinCrew

# 2. Configure Python virtual environment
python3 -m venv backend/.venv
source backend/.venv/bin/activate

# 3. Upgrade pip and install backend dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# 4. Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## 17. Windows Setup Instructions

```powershell
# 1. Clone repository
git clone https://github.com/your-username/FinCrew.git
cd FinCrew

# 2. Configure Python virtual environment
python -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install backend dependencies
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

# 4. Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## 18. PostgreSQL Database Configuration

Every developer cloning FinCrew must set up their own local PostgreSQL database instance. FinCrew uses SQLAlchemy 2.0 with the modern `psycopg` (v3) binary driver.

### Step 1: Ensure PostgreSQL Service is Running
- **macOS (Homebrew):** `brew services start postgresql@16` (or launch Postgres.app)
- **macOS (Postgres.app):** Open Postgres.app and verify the server is running on port 5432.
- **Linux (Ubuntu/Debian):** `sudo systemctl start postgresql`
- **Windows:** Ensure the PostgreSQL Windows Service is started in `services.msc`.

### Step 2: Create the `fincrew_db` Database
Choose one of the following methods depending on your environment:

**Method A: Using the `createdb` command (Fastest on macOS / Linux)**
```bash
createdb fincrew_db
```

**Method B: Using the `psql` command-line shell (Universal)**
```bash
# Connect to default postgres database
psql -U postgres

# Create the dedicated FinCrew database
CREATE DATABASE fincrew_db;

# Verify creation and exit
\l
\q
```

**Method C: Single-command creation**
```bash
psql -U postgres -c "CREATE DATABASE fincrew_db;"
```

---

## 19. Environment Variable Configuration

FinCrew separates sensitive environment settings from application source code. The repository excludes all active `.env` files. You must create your own `backend/.env` before launching the application.

### Step 1: Create Your `backend/.env` File
From the repository root, copy the provided environment template:
```bash
cp .env.example backend/.env
```
*(Alternatively, copy `backend/.env.example` directly to `backend/.env`)*

### Step 2: Customize Database Credentials in `backend/.env`
Open `backend/.env` in your text editor and update `DATABASE_URL` to match your local PostgreSQL credentials:

```ini
# ==============================================================================
# FinCrew Environment Configuration (backend/.env)
# ==============================================================================
APP_NAME=FinCrew
ENV=development
DEBUG=True
PORT=8000

# ------------------------------------------------------------------------------
# PostgreSQL Database Connection URL
# Format: postgresql+psycopg://<username>:<password>@<host>:<port>/<database_name>
# ------------------------------------------------------------------------------
# Option A — Standard PostgreSQL with password:
DATABASE_URL=postgresql+psycopg://postgres:your_actual_password@localhost:5432/fincrew_db

# Option B — macOS (Postgres.app or Homebrew without password):
# DATABASE_URL=postgresql+psycopg://<your_mac_username>@localhost:5432/fincrew_db

# ------------------------------------------------------------------------------
# CORS Allowed Origins (Comma-separated for React / Vite frontend)
# ------------------------------------------------------------------------------
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000

# ------------------------------------------------------------------------------
# Authentication & Cryptographic Signing Key
# ------------------------------------------------------------------------------
# Generate your own unique 32+ character random secret using:
#   openssl rand -hex 32
# or:
#   python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=replace_with_your_own_secure_random_32_character_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Step 3: Run Alembic Database Migrations
Once your `backend/.env` contains your working `DATABASE_URL`, apply Alembic migrations to create the required tables (`users`, `revoked_tokens`, `research_sessions`, `research_reports`):

```bash
cd backend
../backend/.venv/bin/alembic upgrade head
cd ..
```
*(Or with your virtual environment activated: `cd backend && alembic upgrade head && cd ..`)*

**Verify Migration Success:**
```bash
psql -U postgres -d fincrew_db -c "\dt"
```
You should see:
- `users`
- `revoked_tokens`
- `research_sessions`
- `research_reports`
- `alembic_version`

---

## 20. Backend Dependency Installation

Activate your virtual environment and install the verified packages:

```bash
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

Verify that all dependencies are installed without conflicts:
```bash
pip check
```

---

## 21. Frontend Dependency Installation

Navigate to the `frontend/` directory and install the required npm packages:

```bash
cd frontend
npm install
cd ..
```

---

## 22. Running the Backend Server

Start the FastAPI application with Uvicorn:

```bash
# From repository root
PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

The backend server will start at `http://127.0.0.1:8000`.

---

## 23. Running the Frontend Client

In a separate terminal, launch the Vite development server:

```bash
cd frontend
npm run dev
```

The frontend client will be accessible at `http://127.0.0.1:5173`.

---

## 24. Interactive Swagger API Documentation

FastAPI automatically generates interactive OpenAPI documentation. With the backend running, explore the endpoints:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 25. Application User Guide

1. **Authentication**: Register a new account or log in with your credentials. A secure JWT access token is stored in browser memory.
2. **Investment Dashboard**:
   - Inspect workspace KPIs: Total Sessions, Completed Reports, Active Research, and Average Confidence.
   - Monitor portfolio Sector Exposure with dynamic progress bars.
   - Use the horizontal Month Timeline to navigate through historical research periods with animated transitions.
   - Filter reports using the user-controlled Custom Date Range picker or the Sector dropdown.
3. **Initiating Research**:
   - Click **Stock Research** in the top navigation.
   - Enter a stock symbol (e.g. `NVDA`) or click a Quick Pick pill (`AAPL`, `MSFT`, `NVDA`, `GOOGL`, `AMZN`, `TSLA`).
   - Click **Analyze Stock** to dispatch the five specialist agents.
4. **Reviewing Consensus Reports**:
   - Inspect the Current Price, 12-Month Target Price, and Implied Return potential.
   - Switch between specialist tabs: **Consensus**, **Financials**, **Technical**, **Sentiment**, and **Risk**.
5. **Multi-Stock Comparison**:
   - Navigate to **Stock Comparison**.
   - Select between 2 and 5 completed equity sessions to review cross-valuation tables and risk metrics.
6. **Exporting Dossiers**:
   - Click **Export Report** from any completed dossier or history row to download a PDF, JSON, HTML, or Markdown file.

---

## 26. Five-Agent Analysis Lifecycle

```
[User Dispatches Ticker] ──► [Market Data Ingestion & Cache Check]
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
      [Fundamental & Multiples]                    [Technical & Momentum]
      - P/E, EV/EBITDA, P/B, P/S                   - RSI-14 Oscillator
      - Margins & Cash Flow Health                 - 50 / 200 SMA Trend
      - Solvency & Leverage Multiples              - Dynamic Support & Resistance
                   │                                           │
                   └─────────────────────┬─────────────────────┘
                                         ▼
                             [Sentiment & Catalysts]
                             - Financial Lexicon Scoring
                             - Earnings News & Catalysts
                                         │
                                         ▼
                            [Adversarial Risk Severity]
                            - CRO Bear-Case Stress Testing
                            - Volatility Beta & Downside Target
                                         │
                                         ▼
                           [CIO Consensus Synthesis]
                           - Multi-Factor Weighted Scoring
                           - 12-Month Target Price Calculation
                           - Institutional Narrative Compilation
                                         │
                                         ▼
                            [PostgreSQL Persistence]
```

---

## 27. Multi-Format Document Exports (PDF, JSON, HTML, Markdown)

FinCrew provides four export formats for completed research sessions via `GET /api/research/sessions/{session_id}/export?format={format}`:

- **Executive PDF Report (`.pdf`)**: A multi-page institutional memorandum generated via `fpdf2`. Features header branding, rating badges, metric tables, agent breakdowns, and legal disclaimers.
- **Structured JSON Dataset (`.json`)**: Normalized raw data payload containing telemetry metrics, agent scores, and consensus findings for programmatic analysis.
- **Interactive HTML Dossier (`.html`)**: Standalone, responsive HTML document with embedded CSS, accessible tables, and clean typography readable in any web browser.
- **Markdown Briefing Document (`.md`)**: GitHub-flavored Markdown document formatted with structured headers, bulleted evidence points, and markdown tables.

---

## 28. Automated Testing Suite

FinCrew includes a test suite covering authentication, security, market telemetry, multi-agent logic, caching, comparative analysis, and report generation.

Run the test suite from the repository root:

```bash
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests
```

### Test Suite Coverage Breakdown
- `test_agents.py`: Unit tests for the 5 individual specialist agents (10 tests).
- `test_auth.py`: User registration, Bcrypt hashing, JWT lifecycles, token revocation, and user isolation (20 tests).
- `test_market_data.py`: Telemetry fetching, normalization, and ticker validation (8 tests).
- `test_research_api.py`: Synchronous and asynchronous research endpoints and error resilience (11 tests).
- `test_research_models.py`: SQLAlchemy database models and cascading relationship deletes (1 test).
- `test_stage6a_export_and_cache.py`: In-memory cache thread-safety, TTL expiration, and PDF/JSON/HTML/MD export synthesis (12 tests).
- `test_stage6b_compare_and_analytics.py`: Multi-stock comparison logic, validation bounds, and workspace summary metrics (12 tests).

**Total: 74 passing tests (100% pass rate).**

---

## 29. Troubleshooting & FAQ

#### 1. Database connection errors (`psycopg.OperationalError`)
- Ensure PostgreSQL is running on port 5432:
  ```bash
  pg_isready -h localhost -p 5432
  ```
- Verify the connection string in `backend/.env` matches your database name, username, and password.

#### 2. Alembic migration failures
- If tables already exist, synchronize Alembic's revision state:
  ```bash
  cd backend
  ../backend/.venv/bin/alembic stamp head
  cd ..
  ```

#### 3. Market data rate limits (`yfinance` throttling)
- FinCrew includes an automatic in-memory TTL cache (`MarketDataCache`) that preserves market payloads for 5 minutes. If rate limits persist, wait 60 seconds before initiating subsequent analysis.

#### 4. Frontend API connection issues (CORS errors)
- Ensure the backend is running on `http://127.0.0.1:8000` and `CORS_ORIGINS` in `backend/.env` includes `http://localhost:5173,http://127.0.0.1:5173`.

---

## 30. Current Limitations & Future Enhancements

### Current Limitations
- **Coverage**: Focuses on US-listed equities supported by yfinance ticker symbols.
- **Execution Mode**: Research pipeline runs synchronously or via single background tasks per user session.
- **Lexical Sentiment**: News sentiment is evaluated via rule-based financial lexical models.

### Future Enhancements
- **WebSockets / Server-Sent Events (SSE)**: Real-time agent streaming updates during live analysis pipelines.
- **LLM Embeddings & RAG**: Integration of local or hosted LLMs for contextual semantic analysis over quarterly 10-Q/10-K SEC filings.
- **Automated Portfolio Monitoring**: Scheduled email or webhook alerts when consensus ratings or price targets change.
- **Expanded International Equities**: Extended support for London (LSE), Tokyo (TSE), and European exchanges.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
