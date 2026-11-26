# AI-Powered Multi Agent System for Market Analysis and Research

> **Intern Name:** SANJANAA SRINIVASAN  
> **Project Purpose:** Infosys Springboard Virtual Internship 7.0 Batch 5 Project  
> **Module Milestone:** Module 1, Module 2 & Module 3 – User Authentication, Research Workspace, Market Data Collection & Fundamental Analysis Agent  
> **Tech Stack:** React.js, Tailwind CSS, Vite, FastAPI (Python 3.12), PostgreSQL 18, SQLAlchemy 2.0, Alembic, Docker/Uvicorn, yfinance, Scikit-Learn, Jupyter  

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [What is Done (Module 1 Achievements)](#2-what-is-done-module-1-achievements)
3. [What is Done (Module 2 Achievements)](#3-what-is-done-module-2-achievements)
4. [What is Done (Module 3 Achievements - Fundamental Analysis Agent)](#4-what-is-done-module-3-achievements---fundamental-analysis-agent)
5. [Machine Learning Engine (`ml_engine/`) Architecture](#5-machine-learning-engine-ml_engine-architecture)
6. [System Architecture](#6-system-architecture)
7. [User Interface Design & Layouts](#7-user-interface-design--layouts)
   - [Registration Page Wireframe Layout](#registration-page-wireframe-layout)
   - [Stock Research Workspace Dashboard Layout](#stock-research-workspace-dashboard-layout)
   - [Market Analytics & Financial Intelligence Hub Layout](#market-analytics--financial-intelligence-hub-layout)
   - [Fundamental Analysis Agent Screen Layout](#fundamental-analysis-agent-screen-layout)
8. [Prerequisites & Requirements](#8-prerequisites--requirements)
9. [Step-by-Step Installation & Setup](#9-step-by-step-installation--setup)
10. [Project Folder Structure & File-by-File Dictionary](#10-project-folder-structure--file-by-file-dictionary)
11. [Database Schema & Entity Relationships](#11-database-schema--entity-relationships)
12. [Implementation Guide (How It Was Built)](#12-implementation-guide-how-it-was-built)
13. [Google & Apple OAuth 2.0 Configuration](#13-google--apple-oauth-20-configuration)
14. [API Endpoints Reference](#14-api-endpoints-reference)
15. [Automated Testing Suite (Modules 1, 2 & 3)](#15-automated-testing-suite-modules-1-2--3)
16. [License & Acknowledgments](#16-license--acknowledgments)

---

## 1. Project Overview

The **AI-Powered Multi Agent System for Market Analysis and Research** is an enterprise-grade financial intelligence platform. Designed as part of the **Infosys Springboard Virtual Internship 7.0 (Batch 5)**, the system is designed to coordinate multiple specialized autonomous AI agents (Fundamental Analysis, Technical Analysis, News Sentiment Analysis, and Risk Assessment) to conduct rigorous stock market research across global exchanges (NSE, BSE, NASDAQ, NYSE).

**Core System Milestones (Modules 1, 2 & 3):**
- **Authentication Engine:** Multi-factor authentication with bcrypt 12-round password hashing and OAuth 2.0 (Google & Apple) identity federation.
- **Session Security:** Cryptographically signed JSON Web Tokens (JWT) transmitted inside tamper-proof, HTTP-only cookies with strict CORS protection.
- **Relational Data Layer:** PostgreSQL schema with 8 relational tables linked via UUIDs, foreign keys, and cascade deletion rules.
- **Fintech Research Workspace:** Dark-theme responsive UI with live password validation, company and ticker search without fabricated data, watchlist management, user research history, and user preferences persistence.
- **Market Data Pipeline & Analytics Hub (Module 2):** Real-time market data ingestion across global exchanges (NSE, BSE, NASDAQ, NYSE), instant keystroke auto-suggest, multi-timeframe OHLCV historical candlestick data collection, Time Series Analysis (SMA 20, SMA 50, annualized rolling volatility, trend direction), return distribution histograms, company profiles, and multi-year financial statements.
- **Fundamental Analysis Agent & ML Engine (Module 3):** Full-screen autonomous financial condition analysis across 7 core pillars (Revenue/Earnings Trajectory, Profitability Margins, Debt & Solvency Risk Gauges, Valuation Multiples, Historical Financial Statements Breakdown, Peer Benchmarking with Dual Search Autocomplete, and Transparent Data Audit). Powered by a structured Machine Learning repository (`ml_engine/`) containing financial ratio datasets, a training Jupyter notebook, and serialized model/scaler artifacts.

---

## 2. What is Done (Module 1 Achievements)

### 1. User Registration & Security Checklist
- Built registration form with `Full Name`, `Email Address`, `Password`, and `Confirm Password`.
- Real-time client-side password strength checker verifying:
  - Minimum 8 characters.
  - At least one uppercase letter.
  - At least one lowercase letter.
  - At least one number.
  - At least one special symbol (`!@#$%^&*`).
- Backend password hashing using direct `bcrypt` cryptographic salt and hash (12 rounds).
- Prevention of duplicate account registrations (returns HTTP 400 with clean user error).

### 2. User Login & Credential Verification
- Authenticates email and password against stored `bcrypt` hash in PostgreSQL `users` table.
- Issues secure JSON Web Tokens (JWT) containing `user_id` and token expiration (`exp`).
- Transmits JWT via `Set-Cookie` with `HttpOnly`, `SameSite=Lax`, and `Secure` attributes to prevent XSS credential theft.

### 3. Social Authentication (Google OAuth 2.0 & Apple Sign-In)
- Full OAuth 2.0 authorization code grant flow with Google Cloud Identity platform.
- Apple Sign-In callback integration.
- Unified identity model: auto-creates or links user accounts in the `users` and `user_auth_accounts` tables.

### 4. Fintech Research Workspace Dashboard
- Personalized user greeting displaying the authenticated user's name derived strictly from the backend JWT session.
- Frameless, seamless dark fintech aesthetic matching official UI specifications (`#05080a`, `#0b0f15`, `#00d084`).
- **Research Agents Section:** 4 interactive agent cards with status indicators (Fundamental Analysis Agent active; Technical, News, and Risk agents scheduled).

### 5. Real Stock Search, Live Market Pricing & Currency Awareness
- **Real-Time Ticker Search:** Search by company name or ticker symbol across NSE, BSE, NASDAQ, and NYSE (e.g., Apple `AAPL`, Reliance `RELIANCE`, Infosys `INFY`, Tata Consultancy Services `TCS`, Microsoft `MSFT`).
- **Live Real-Time Market Data:** Tickers are enriched with live trading prices, previous close calculations, and real percentage changes (`+`/`-`).
- **Currency Intelligence:** Automatically detects market currency:
  - Indian stocks (NSE/BSE) are tagged with a green **INR** badge.
  - American stocks (NASDAQ/NYSE) are tagged with an amber **USD** badge.
- **USD Currency Confirmation Safety Modal:** When interacting with American stocks (adding to watchlist or initiating research), an amber modal prompts: *"Currency Notice - Are you sure? This stock is on a US exchange. All prices and financial data are quoted in US Dollars ($ USD)."* with an explicit confirmation step.
- **Watchlist Operations:** Add ticker to user's saved stocks with live price updates, view all saved stocks, remove stock with instant optimistic UI update, and launch research directly from saved items.
- Duplicate prevention enforced both at database constraint level (`UNIQUE(user_id, ticker)`) and in FastAPI route.

### 6. User-Specific Research History
- Records every research launch in PostgreSQL `research_tasks` linked to the authenticated `user_id`.
- Automatically fetches real market fundamentals (52-week high/low, market capitalization, trailing P/E ratio, trading volume) into the synthesized research report.
- Displays Company Name, Stock Ticker, Market Exchange, Analysis Period, Creation Date, and Status (`Pending`, `Processing`, `Completed`, `Failed`).
- Built-in report modal allowing users to inspect the generated stock research report.

### 7. User Preferences (Market & Analysis Period)
- Persistent preference controls for:
  - **Market:** `NSE` (India), `BSE` (India), `NASDAQ` (US), `NYSE` (US).
  - **Analysis Period:** `1 Month`, `3 Months`, `6 Months`, `1 Year`, `5 Years`.
- Stored in dedicated PostgreSQL table `user_preferences` and auto-populated when opening research tasks.
- Validated server-side against supported market exchange conventions.

---

## 3. What is Done (Module 2 Achievements)

### Stock Search and Market Data Collection

#### 1. Search for Companies Using Their Name or Ticker Symbol
- Real-time stock search supporting both company names (e.g., Apple, Infosys, Reliance, Microsoft) and official ticker symbols (e.g., AAPL, INFY, RELIANCE, MSFT).
- Features instant 0ms auto-suggest from a verified market catalog as the user types, combined with debounced live search querying global market directories.
- Clean interaction model allowing users to directly click any company card to open analytics without unnecessary buttons.

#### 2. Retrieve Historical Stock Prices
- Endpoints and services to fetch historical trading records across standardized periods: 1 Month (1mo), 3 Months (3mo), 6 Months (6mo), 1 Year (1y), and 5 Years (5y).
- Supports bar intervals including 1-day (1d) and 1-week (1wk) resolution.
- Standardizes user period selections with automatic symbol fallback for Indian equities (.NS).

#### 3. Collect OHLCV Data: Open, High, Low, Close, and Volume
- Standardized data collection capturing complete time series candle dimensions: Open, High, Low, Close, and Volume.
- Calculates daily percentage price changes against previous closing prices.
- Formats reverse-chronological historical tables and provides one-click client-side CSV export of collected OHLCV records.

#### 4. Retrieve Available Company Profiles and Financial Statements
- Retrieves available corporate overview data: business description, sector, industry classification, country, official website, and executive leadership officers.
- Gathers key market valuation multiples including Market Capitalization, Trailing P/E, Forward P/E, 52-Week High, 52-Week Low, Beta, and Dividend Yield.
- Ingests available multi-year financial statements: Income Statement, Balance Sheet, and Cash Flow Statement.

#### 5. Record Data Sources and Retrieval Timestamps
- Explicitly records data provenance on every market payload and research report: tagged with Data Source: yfinance API.
- Captures exact retrieval timestamps with high precision (YYYY-MM-DD HH:mm:ss IST).
- Stamps report generation dates across analytical modal headers, metadata footers, and report exports.

#### 6. Support the Selected Stock Market, such as NSE/BSE or NYSE/Nasdaq
- Dynamic multi-market classification supporting Indian exchanges (NSE, BSE) and American exchanges (NASDAQ, NYSE).
- Automatically assigns exchange tags and currency indicators: Indian Rupee (INR) with green tags and US Dollar (USD) with amber tags.
- Includes a dedicated USD Currency Warning Modal that confirms user intent and clarifies dollar denominations when interacting with US market equities.

---

## 4. What is Done (Module 3 Achievements - Fundamental Analysis Agent)

### Autonomous Financial Reasoning & 7 Core Features

#### Official Specification Overview:
> **Fundamental Analysis Agent:**  
> This agent analyzes the financial performance and condition of a company.  
> **Features:**  
> • Revenue and earnings analysis.  
> • Profitability analysis.  
> • Debt and financial stability analysis.  
> • Calculation of financial ratios such as P/E, P/B, and ROE when the required data is available.  
> • Historical financial performance comparison.  
> • Peer comparison where comparable data is available.  
> • Identification of missing or inconsistent financial information.  
>  
> **Example:** When a user searches for a company, the agent retrieves available financial data and explains its revenue growth, profitability, debt levels, and relevant valuation metrics.

#### 0. Company Overview Header Card
- Displays live stock price, currency indicator (`$`, `₹`), 52-week high/low range meter with visual percentile gradient bar, market capitalization, employee count, sector, industry, and corporate website.
- Features an expandable corporate summary toggle (`"Read more / Show less"`) preserving sleek visual density.

#### 1. Revenue and Earnings Analysis (Feature 1)
- Multi-year revenue and net income trajectory chart across up to 4 consecutive fiscal years.
- Interactive metric switcher tabs allowing the analyst to toggle between **`[All]`**, **`[Revenue]`**, **`[Net Income]`**, and **`[EBITDA]`**.
- Features prominent YoY revenue momentum badge (e.g. `↗ +4.57% YoY`) and dynamic hover tooltips displaying exact formatted figures (`₹1,821.20 Cr`).
- Built with CSS flexbox `h-full justify-end` and percentage clamping, guaranteeing that bars render visibly across all selected tabs without collapsing.

#### 2. Profitability Analysis (Feature 2)
- Evaluates operational return efficiencies across Gross Margin, Operating Margin, Net Profit Margin, Return on Equity (ROE), and Return on Assets (ROA).
- Each progress bar incorporates vertical industry benchmark reference lines and assigns green `"Above avg"` tags to outperforming metrics.

#### 3. Debt and Financial Stability Analysis (Feature 3)
- **Debt-to-Equity Meter:** Visual risk gauge evaluating balance sheet leverage across `Safe` (< 0.5), `Moderate` (0.5–1.0), and `Elevated` (> 1.0) zones.
- **Current Ratio (Liquidity) Meter:** Evaluates short-term solvency across `Strong` (≥ 2.0x), `Healthy` (≥ 1.5x), `Adequate` (≥ 1.0x), and `Weak` (< 1.0x) liquidity zones.
- Validates reported accounting profits against real Operating Cash Flow.

#### 4. Calculation of Financial Ratios (Feature 4)
- Responsive 6-card valuation and efficiency grid displaying **P/E Ratio** (TTM), **P/B Ratio**, **EPS** (Earnings Per Share), **ROA**, **Gross Margin**, and **Solvency Assessment**.

#### 5. Historical Financial Performance Comparison (Feature 5)
- Tabular breakdown comparing historical fiscal years side-by-side with Total Revenue, Net Income, EBITDA, and Operating Cash Flow.
- Summary trajectory cards breaking down annual milestones and operational growth trends.

#### 6. Peer Comparison & Dual Search Engine (Feature 6)
- **Sector Peer Catalog:** Pre-configures verified peers across technology, financial, automotive, and healthcare sectors.
- **Dual-Search Autocomplete Engine:** Typing in custom peer search (e.g. "Apple", "TCS", "Wipro") offers 0ms local catalog matching + debounced live API search (`stockService.search`), supporting both US and Indian markets.
- **Plain-English Competitive Narrative:** Automatically synthesizes a plain-English explanation of valuation discount/premiums, margin standing, and balance sheet safety.
- **Comparative Visual Bars & Advantage Badges:** Side-by-side metric comparison bars with green advantage pills indicating the market leader for each metric.

#### 7. Identification of Missing or Inconsistent Information (Feature 7)
- Scans filing statements for mandatory line items.
- When specific non-mandatory items (such as standalone R&D breakdown) are absent, it renders a transparent amber notice:
  > *"We retrieved all available information from official filings, but unfortunately we could not find data for [Research & Development (R&D) Expense Breakdown]. All other fundamental metrics were verified."*
- Features an accounting footnote clarifying that under Indian GAAP / Ind AS, IT engineering costs are filed under *Employee Benefit Expenses* and *Cost of Technical Subcontractors*.
- Equipped with an **`X`** close button to dismiss the banner once reviewed.

#### 8. Research Report Synthesis Integration & Individual Deletion
- Section 2 of the Multi-Agent Research Dossier is updated dynamically with the Fundamental Agent's findings.
- Users can delete research reports individually with cascading deletion across database records.

#### 9. Corporate-Grade PDF Engine
- Generates publication-ready PDF exports with proper hanging indents for multi-line bullets, bold key labels, 15 pt separation below section headers, and clean ASCII currency formatting (`INR (Rs.)`).

---

## 5. Machine Learning Engine (`ml_engine/`) Architecture

The project contains a dedicated Machine Learning and financial data modeling repository located under **`ml_engine/`**:

```
MULTI-AGENT STOCK RESEARCH ANALYST/
└── ml_engine/
    ├── data/
    │   └── Financial Statements.csv          <- Kaggle: Financial Statements of Major Companies (2009-2023)
    ├── notebooks/
    │   └── Fundamental_Analysis_ML.ipynb     <- Jupyter notebook for EDA, training & validation
    └── models/
        ├── fundamental_analysis_model.pkl    <- Trained scikit-learn classifier / scoring estimator
        ├── fundamental_features.pkl          <- Serialized list of input feature names
        └── fundamental_scaler.pkl            <- Pre-fitted StandardScaler normalization transformer
```

### 1. Dataset (`ml_engine/data/Financial Statements.csv`)
- **Source:** [Financial Statements of Major Companies (2009-2023)](https://www.kaggle.com/datasets/rish59/financial-statements-of-major-companies2009-2023) — sourced from Kaggle, used to train the Fundamental Analysis Agent's Logistic Regression financial health classifier.
- **Coverage:** Comprehensive multi-company tabular dataset compiling audited financial statement metrics across global equities.
- **Attributes:** Total Revenue, Gross Margin, Operating Margin, Net Profit Margin, Debt-to-Equity, Current Ratio, P/E Ratio, P/B Ratio, Return on Equity (ROE), and assigned financial health classification.
- **Purpose:** Supplies statistical distributions and baseline ratios for model training and comparative benchmarking.

### 2. Jupyter Notebook (`ml_engine/notebooks/Fundamental_Analysis_ML.ipynb`)
- **Exploratory Data Analysis (EDA):** Statistical summary of financial ratios, skewness analysis, and correlation heatmaps between debt leverage, operating margins, and corporate return on equity.
- **Data Preprocessing:** Imputation of missing disclosures, outlier mitigation, and feature standardization via Scikit-Learn `StandardScaler`:
  $$z = \frac{x - \mu}{\sigma}$$
- **Model Training & Evaluation:** Evaluates classification algorithms (Logistic Regression, K-Nearest Neighbors, Random Forest), performs stratified 80/20 train-test split, and serializes the champion Logistic Regression model weights.

### 3. Serialized Model Artifacts (`ml_engine/models/*.pkl`)
- **`fundamental_analysis_model.pkl`:** The trained Logistic Regression estimator (`max_iter=1000, random_state=42`) predicting financial health reliability scores (e.g. `96.97% Reliability Score`).
- **`fundamental_scaler.pkl`:** Preserves feature means and standard deviations to transform incoming live metrics into the model's standardized feature space.
- **`fundamental_features.pkl`:** Preserves exact feature column ordering, guaranteeing consistency during inference.

### 4. Real-Time yfinance Inference Bridge
- In `backend/app/utils/fundamental_agent.py`, the backend bridges live market data into the financial model:
  1. Fetches real-time financial statements and ratios via `yfinance`.
  2. Computes the ratio vector (Revenue Growth, Operating Margin, Debt-to-Equity, Current Ratio, P/E, P/B, ROE).
  3. Applies `fundamental_scaler.transform()` and executes `fundamental_analysis_model.predict()`.
  4. Synthesizes the statistical verdict with live fundamental rules into verified health scores.

---

## 6. System Architecture

The full-stack application follows a decoupled 5-layer integration architecture:

```
+------------------------------------------------------------------------+
|                  1. CLIENT APPLICATION (React 18 + Vite)               |
|  - Dark Fintech UI (#05080a, Tailwind CSS)                             |
|  - Auth Pages (Login/Register) with Live 5-Rule Password Validation    |
|  - Research Workspace (Watchlist, Preferences, Search, Recent Tasks)   |
|  - Market Analytics Hub (Interactive Charts, OHLCV, Profile, Fin.)     |
|  - Fundamental Analysis Agent Screen (7 Features, Dynamic Charts)      |
|  - Axios HTTP Client with withCredentials: true & jsPDF Report Export  |
+-----------------------------------+------------------------------------+
                                    | HTTP / JSON (via Vite /api Reverse Proxy)
                                    v
+------------------------------------------------------------------------+
|             2. API GATEWAY & SECURITY (FastAPI + Uvicorn)              |
|  - Routers: /api/auth, /api/stocks, /api/dashboard                     |
|  - Fundamental Agent Engine: /api/stocks/{ticker}/fundamental          |
|  - Bcrypt 12-Round Salt Password Hashing & Verification                |
|  - JWT Cookie Session Guard: Set-Cookie (HttpOnly, SameSite=Lax)       |
|  - Dependency Injection: get_current_user Authenticated Principal      |
+-------------------+--------------------+-------------------------------+
                    |                    |                               |
                    v                    v                               v
+------------------------------------+ +-------------------------------+ +-------------------------------+
|     3. RELATIONAL DATA LAYER       | |    4. EXTERNAL INTEGRATIONS   | |     5. MACHINE LEARNING       |
|         (PostgreSQL 18)            | |                               | |       ENGINE (ml_engine/)     |
|  - SQLAlchemy 2.0 ORM Engine       | |  - Google Cloud Identity      | |  - Financial Statements.csv   |
|    (Kaggle Dataset 2009-2023) |
|  - 8 Connected Relational Tables   | |    OAuth 2.0 Redirect & Code  | |  - Fundamental_Analysis_ML.ipynb|
|  - UUID Primary Keys & Cascades    | |  - Apple Sign-In OAuth Flow   | |  - Serialized Models (*.pkl)  |
|  - agent_results & research_reports| |  - Live Stock Market Feeds    | |  - Logistic Regression Inference|
+------------------------------------+ +-------------------------------+ +-------------------------------+
```

---

## 7. User Interface Design & Layouts

### Registration Page Wireframe Layout
```
+--------------------------------------+------------------------------------------+
| LEFT COLUMN: Branding & Value        | RIGHT COLUMN: Interactive Form           |
|                                      |                                          |
| Multi-Agent Stock Research Analyst   |  Create Your Research Account            |
| "Empowering investors through        |  Full Name       [ Sanjanaa Srinivasan ] |
|  collaborative AI intelligence"      |  Email Address   [ user@example.com    ] |
|                                      |  Password        [ ****************    ] |
| - Multi-Agent Analysis               |  Confirm Pass    [ ****************    ] |
| - Real-Time Market Insights          |                                          |
| - Secure & Personalized Session      |  LIVE PASSWORD COMPLEXITY CHECKLIST:     |
|                                      |  [x] At least 8 characters               |
| [Digital Globe & Market Artwork]     |  [x] Uppercase & Lowercase letter        |
|                                      |  [x] At least one number                 |
|                                      |  [x] Special character (!@#$%^&*)        |
|                                      |                                          |
|                                      |  [       Create Account Button       ]   |
|                                      |  --- or continue with Google / Apple --- |
+--------------------------------------+------------------------------------------+
```

---

### Stock Research Workspace Dashboard Layout
```
+---------------------------------------------------------------------------------+
| [Logo] Multi-Agent Stock Analyst          [Search Shortcut]   (SS) [ Sign Out ] |
+---------------------------------------------------------------------------------+
| Welcome back, Sanjanaa Srinivasan!                                              |
| Track saved stocks, analyze companies across exchanges, and run AI research.   |
+---------------------------------------------------------------------------------+
| PREFERENCES:  Market: [ NSE (India) v ]   Horizon: [ 6 Months v ]   [ Save ]    |
+---------------------------------------------------------------------------------+
| SEARCH: [ Enter company name or ticker (e.g. INFY, AAPL, TCS) ... ]             |
| Live Auto-Suggest: [ Infosys Limited (INFY.NS) - NSE - Rs.1,103.40 INR ]        |
| Quick Picks: [ RELIANCE ]  [ TCS ]  [ INFY.NS ]  [ AAPL ]  [ MSFT ]             |
|                                                                                 |
| +-----------------------------------------------------------------------------+ |
| | INFY.NS  Infosys Limited   [NSE (India)]  [INR]   Rs.1,103.40 (+1.25%)      | |
| | (Direct-click card to view Market Analytics Hub)                            | |
| | [ Launch Fundamental Agent ]   [ Research ]   [ + Watchlist ]               | |
| +-----------------------------------------------------------------------------+ |
+---------------------------------------------------------------------------------+
| AI RESEARCH AGENTS (Module Pipeline)                                            |
| +------------------+ +------------------+ +------------------+ +--------------+ |
| | Fundamental Agent| | Technical Agent  | | Sentiment Agent  | | Risk Analyst | |
| | [ACTIVE - Launch]| | [Coming Soon]    | | [Coming Soon]    | | [Coming Soon]| |
| +------------------+ +------------------+ +------------------+ +--------------+ |
+----------------------------------------+----------------------------------------+
| WATCHLIST (SAVED STOCKS)               | RECENT RESEARCH HISTORY                |
| - INFY.NS  Rs.1,103.40 [Analyze] [Del] | - AAPL | NASDAQ | 1 Year | [Completed] |
| - AAPL     $228.40     [Analyze] [Del] | - INFY | NSE    | 6 Mo   | [Completed] |
+----------------------------------------+----------------------------------------+
```

---

### Market Analytics & Financial Intelligence Hub Layout
```
+---------------------------------------------------------------------------------+
| [INFY.NS] Infosys Limited               NSE (India) - INR - Current: Rs.1,103.40|
| [BULLISH TREND]                         Horizon: [1M] [3M] [6M] [1Y] [5Y] [X]   |
+---------------------------------------------------------------------------------+
| [SUB-TAB 1: CHARTS] [SUB-TAB 2: OHLCV] [SUB-TAB 3: PROFILE] [SUB-TAB 4: FIN.]   |
+---------------------------------------------------------------------------------+
| ACTIVE TAB VIEW:                                                                |
| - Price Chart: Candlestick/Area + SMA 20 (Cyan) + SMA 50 (Purple)               |
| - Daily Returns Histogram: 10 frequency bins showing price movement spread      |
| - OHLCV Table: Date, Open, High, Low, Close, Volume, Change % + [Export CSV]    |
| - Company Profile: Business summary, Sector, Industry, Multiples, Officers     |
| - Financial Statements: Income Statement, Balance Sheet, Cash Flow multi-year  |
+---------------------------------------------------------------------------------+
| Data Source: yfinance API  |  Retrieved At: 2026-11-24 19:47:11 IST             |
+---------------------------------------------------------------------------------+
```

---

### Fundamental Analysis Agent Screen Layout
```
+---------------------------------------------------------------------------------+
| [<- Back to Dashboard]  INFOSYS LIMITED (INFY.NS)     [HEALTHY CONDITION]  [R]  |
+---------------------------------------------------------------------------------+
| [COMPANY OVERVIEW CARD]                                                         |
| Price: Rs.1,103.40 | 52W Range: [========|===] (Rs.980 - Rs.1,728) | MCap: 4.8L |
| Summary: Leading provider of digital consulting, cloud & AI-first solutions...  |
+---------------------------------------------------------------------------------+
| ⚠️ DATA AUDIT NOTICE: Missing Standalone R&D Breakdown (Ind AS Reporting)   [X] |
+----------------------------------------+----------------------------------------+
| [REVENUE & EARNINGS TRAJECTORY]        | [PROFITABILITY MARGINS]                |
| Metric Tabs: [All] [Rev] [NI] [EBITDA] | Gross Margin: 34.50% [Above avg]       |
| YoY Growth: ↗ +4.57%                   | Operating: 21.14% | Net Margin: 16.44% |
| Bar Chart (FY23 -> FY26) with Tooltips | ROE: 33.85% | ROA: 18.20%              |
+----------------------------------------+----------------------------------------+
| [SOLVENCY & FINANCIAL HEALTH GAUGES]   | [VALUATION MULTIPLES GRID]             |
| Debt-to-Equity: 0.10 (Safe Zone)       | P/E: 14.70x | P/B: 4.59x | EPS: Rs.75  |
| Current Ratio: 1.98x (Strong Liquidity)| ROA: 18.20% | Gross Margin: 34.50%     |
+----------------------------------------+----------------------------------------+
| [PEER BENCHMARKING & DUAL SEARCH AUTOCOMPLETE]                                  |
| Peer: [Tata Consultancy Services (TCS.NS) v] or [+ Custom Peer Search...]       |
| Narrative: "INFY.NS trades at P/E 14.70x (-45.2% discount) vs TCS.NS 26.80x..." |
| Side-by-Side Comparative Metric Bars with Leading Advantage Badges              |
+---------------------------------------------------------------------------------+
| [HISTORICAL FINANCIAL STATEMENTS BREAKDOWN TABLE]                               |
| FY23 | Revenue: Rs.1,821 Cr | Net Income: Rs.298 Cr | EBITDA: Rs.468 Cr | OCF   |
| FY24 | Revenue: Rs.1,856 Cr | Net Income: Rs.317 Cr | EBITDA: Rs.497 Cr | OCF   |
| FY25 | Revenue: Rs.1,928 Cr | Net Income: Rs.316 Cr | EBITDA: Rs.507 Cr | OCF   |
| FY26 | Revenue: Rs.2,015 Cr | Net Income: Rs.331 Cr | EBITDA: Rs.511 Cr | OCF   |
+---------------------------------------------------------------------------------+
```

---

## 8. Prerequisites & Requirements

Before running the project, verify that the following dependencies are installed:

| Requirement | Minimum Version | Verified Version | Purpose |
|---|---|---|---|
| **Python** | 3.10+ | 3.12.x | Backend runtime, FastAPI server & Scikit-Learn |
| **Node.js** | 18.0+ | 20.x / 22.x | Frontend runtime environment |
| **npm** or **pnpm** | 9.0+ | npm 10.x | Package manager |
| **PostgreSQL** | 14.0+ | PostgreSQL 18 | Relational database management system |
| **Git** | 2.x | 2.4x | Version control |

---

## 9. Step-by-Step Installation & Setup

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
   # PostgreSQL connection string
   DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/multi_agent_stock_db

   # Cryptographic JWT Secret Key
   SECRET_KEY=your_secure_jwt_secret_key_here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ENVIRONMENT=development

   # Frontend and Backend URLs
   FRONTEND_URL=http://localhost:5173
   BACKEND_URL=http://localhost:8000

   # Google OAuth 2.0 Credentials
   GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

   # Apple Sign-In Credentials (optional)
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
   VITE_API_BASE_URL=
   ```

4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   - Frontend Application URL: `http://localhost:5173`

---

## 10. Project Folder Structure & File-by-File Dictionary

```
MULTI-AGENT STOCK RESEARCH ANALYST/
|-- backend/
|   |-- alembic/
|   |   |-- versions/
|   |   |   `-- 20261111_01_init_all_tables.py  # Alembic migration for all 8 database tables
|   |   |-- env.py                             # Alembic runtime config connecting SQLAlchemy models
|   |   `-- script.py.mako                     # Template for generating future migrations
|   |-- app/
|   |   |-- __init__.py                        # Python package marker
|   |   |-- main.py                            # FastAPI entry point, CORS config, lifespan lifecycle
|   |   |-- database.py                        # SQLAlchemy engine, session maker, get_db() dependency
|   |   |-- models.py                          # 8 SQLAlchemy models with UUIDs, FKs, and cascades
|   |   |-- schemas.py                         # Pydantic v2 validation models for request/response bodies
|   |   |-- auth.py                            # bcrypt password hashing, JWT creation, cookie config
|   |   |-- dependencies.py                    # get_current_user security guard reading cookie/header
|   |   |-- oauth.py                           # Google & Apple OAuth flow helpers and token exchange
|   |   |-- utils/
|   |   |   |-- fundamental_agent.py           # Module 3 Fundamental Analysis Agent & ratio engine
|   |   |   `-- time_series_analysis.py        # TSA engine (SMA 20/50, volatility, histogram bins)
|   |   `-- routes/
|   |       |-- __init__.py                    # Route package marker
|   |       |-- auth_routes.py                 # /register, /login, /logout, /me endpoints
|   |       |-- oauth_routes.py                # Google & Apple login and callback redirect endpoints
|   |       |-- stock_routes.py                # /search, /historical, /profile, /financials, /fundamental
|   |       `-- dashboard_routes.py            # /watchlist, /research, and /preferences endpoints
|   |-- alembic.ini                            # Alembic database migration settings
|   |-- requirements.txt                       # Backend Python dependencies list
|   |-- .env.example                           # Sample template for backend environment variables
|   |-- .env                                   # Active backend environment variables (Postgres & OAuth)
|   |-- verify_db.py                           # Verification script to inspect tables and connectivity
|   |-- test_e2e_full.py                       # Automated test suite with 14 end-to-end integration tests
|   |-- test_module_2.py                       # Module 2 verification suite (OHLCV, TSA, Profile, Fin.)
|   `-- test_module_3.py                       # Module 3 verification suite (Fundamental Agent & 7 features)
|
|-- frontend/
|   |-- public/
|   |   `-- images/
|   |       |-- financial-globe.png            # Frameless digital globe & candlesticks artwork (Auth)
|   |       `-- dashboard-globe.png            # Clean financial chart graphic (Dashboard Welcome)
|   |-- src/
|   |   |-- components/
|   |   |   |-- AuthLayout.jsx                 # 2-column responsive layout with branding and graphic
|   |   |   |-- Navbar.jsx                     # Top navigation bar with logo, user avatar & logout
|   |   |   |-- ProtectedRoute.jsx             # React Router guard redirecting unauthenticated users
|   |   |   |-- AgentCard.jsx                  # UI card for research agents (Active Fundamental Agent)
|   |   |   |-- StockSearch.jsx                # Search bar, 0ms auto-suggest, card direct-click
|   |   |   |-- StockAnalyticsHub.jsx          # Multi-tab financial analytics hub modal (Module 2)
|   |   |   |-- FundamentalAnalysisModal.jsx   # Module 3 Fundamental Agent Interface (7 features & tabs)
|   |   |   |-- StructuredReportViewer.jsx     # Clean 8-section research report viewer
|   |   |   `-- SocialLogin.jsx                # "Continue with Google" and "Sign in with Apple" buttons
|   |   |-- pages/
|   |   |   |-- Login.jsx                      # Login page with email, password, and social buttons
|   |   |   |-- Register.jsx                   # Registration page with live password checklist
|   |   |   `-- Dashboard.jsx                  # Main workspace with preferences, agents, watchlist, history
|   |   |-- context/
|   |   |   `-- AuthContext.jsx                # Global authentication state (user, login, logout, checkAuth)
|   |   |-- services/
|   |   |   `-- api.js                         # Axios client with withCredentials: true and API endpoints
|   |   |-- App.jsx                            # Router definition connecting Login, Register, Dashboard
|   |   |-- main.jsx                           # React DOM mount point wrapped with BrowserRouter
|   |   `-- index.css                          # Tailwind CSS base directives and dark background colors
|   |-- index.html                             # Single page HTML entry point
|   |-- package.json                           # Frontend dependencies and scripts (dev, build, preview)
|   |-- tailwind.config.js                     # Tailwind theme customization (emerald & dark colors)
|   |-- vite.config.js                         # Vite server configuration with reverse proxy for /api
|   |-- .env.example                           # Frontend environment template
|   `-- .env                                   # Frontend active environment variables
|
|-- ml_engine/                                 # Machine Learning & Financial Modeling Engine
|   |-- data/
|   |   `-- Financial Statements.csv           # Kaggle: Financial Statements of Major Companies (2009-2023) - Training data for Fundamental Analysis Agent
|   |-- notebooks/
|   |   `-- Fundamental_Analysis_ML.ipynb         # Jupyter Notebook for EDA, data preprocessing, scaling, training
|   `-- models/
|       |-- fundamental_analysis_model.pkl     # Trained Scikit-Learn financial condition estimator
|       |-- fundamental_features.pkl           # Serialized feature column ordering schema
|       `-- fundamental_scaler.pkl             # Pre-fitted StandardScaler normalization artifact
|
|-- generate_diagrams.py                       # Automated diagram engine generating all 9 PNG diagrams
|-- .gitignore                                 # Git ignore file for Python cache, node_modules, and .env
`-- README.md                                  # Complete Project Master Documentation
```

---

## 11. Database Schema & Entity Relationships

The PostgreSQL database `multi_agent_stock_db` stores all information using relational tables connected via UUID primary keys and foreign keys:

| Table Name | Primary Key | Foreign Keys | Description and Table Uses |
|---|---|---|---|
| `users` | `user_id` (UUID) | `email` (UNIQUE, Indexed) | Core user identity table. Stores user profile information, full name, unique email address, and 12-round bcrypt password hash. Used to authenticate users, protect sessions, and isolate personal workspace data. |
| `user_auth_accounts` | `auth_id` (UUID) | `user_id` -> `users.user_id`<br>`UNIQUE(provider, provider_user_id)` | Federated social login table. Stores third-party OAuth 2.0 account associations (Google subject ID and Apple ID) linked to the primary user record for single sign-on access. |
| `user_preferences` | `preference_id` (UUID) | `user_id` -> `users.user_id`<br>`UNIQUE(user_id)` | User settings persistence table. Stores each user's default preferred market exchange (NSE, BSE, NASDAQ, NYSE) and analysis time horizon (1 Month, 3 Months, 6 Months, 1 Year, 5 Years). Auto-selects default ticker in Fundamental Agent. |
| `saved_stocks` | `saved_stock_id` (UUID) | `user_id` -> `users.user_id`<br>`UNIQUE(user_id, ticker)` | User watchlist table. Stores stock ticker symbols bookmarked by the user. The unique constraint prevents duplicate stocks per user. Used by the dashboard to render the user's active watchlist with live pricing and daily percentage movements. |
| `research_tasks` | `task_id` (UUID) | `user_id` -> `users.user_id` | Research execution audit table. Tracks stock research requests launched by users, storing the ticker, exchange, requested period, execution status (Pending, Completed, Failed), and timestamps. |
| `research_reports` | `report_id` (UUID) | `task_id` -> `research_tasks.task_id` | Research synthesis storage table. Stores the comprehensive research report content, executive summary, analytical limitations, and data source timestamps. Section 2 is populated with Fundamental Agent findings. |
| `agent_results` | `result_id` (UUID) | `task_id` -> `research_tasks.task_id` | Agent payload table. Actively persisted on `POST /api/dashboard/research` storing `agent_name="Fundamental Analysis Agent"`, `status`, and the full `output_json` (JSONB) payload. |
| `source_documents` | `source_id` (UUID) | `task_id` -> `research_tasks.task_id` | Provenance and source audit table. Actively persisted on `POST /api/dashboard/research` storing `source_type="yfinance API"`, `title`, `source_url`, and `retrieved_at` timestamps. |

---

## 12. Implementation Guide (How It Was Built)

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
- The token is placed inside an HTTP-only cookie named `access_token` with `httponly=True`, `samesite="lax"`.
- **Why this is secure:** JavaScript running in the browser cannot access HTTP-only cookies, making the session completely immune to Cross-Site Scripting (XSS) token theft.

### 3. Server-Side Identity Derivation
- To prevent privilege escalation attacks, the frontend **never** sends `user_id` in request bodies.
- FastAPI's `get_current_user` dependency automatically extracts and decodes the JWT from the cookie.

### 4. Real-Time Time Series Analysis Pipeline (Module 2)
- Historical candlestick data is analyzed on the fly by `compute_time_series_analysis()`. The engine calculates rolling 20-day and 50-day Simple Moving Averages, annualized volatility from daily return variance, directional trend momentum, and 10-bin frequency distribution histograms.

### 5. Fundamental Analysis Agent & Ratio Engine (Module 3)
- Implemented in `backend/app/utils/fundamental_agent.py` and accessed via `GET /api/stocks/{ticker}/fundamental`.
- Computes all 7 core features with real-time financial statements, balance sheets, and cash flows.
- Features graceful fallbacks, narrative comparative synthesis, and accounting-aware data audit notices.

---

## 13. Google & Apple OAuth 2.0 Configuration

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

## 14. API Endpoints Reference

The FastAPI backend exposes **23 unique REST API endpoints** structured across 5 route modules (with `10e` documenting the optional `?peer=` query mode):

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

### 4. Stock Search, Historical Feeds & Financial Analytics (`/api/stocks`) (4 Endpoints)
| # | HTTP Method | Endpoint URL | Description | Access Level |
|---|---|---|---|---|
| 10 | `GET` | `/api/stocks/search?q={query}` | Search real tickers across NSE, BSE, NASDAQ, NYSE with live prices | Public |
| 10a | `GET` | `/api/stocks/{ticker}/historical?period={period}` | Retrieve OHLCV prices, TSA (SMA 20/50, Volatility), and return histogram | Public |
| 10b | `GET` | `/api/stocks/{ticker}/profile` | Retrieve company profile, sector, industry, valuation ratios & executives | Public |
| 10c | `GET` | `/api/stocks/{ticker}/financials` | Retrieve Income Statement, Balance Sheet, and Cash Flow statements | Public |

### 5. Fundamental Analysis Agent (`/api/stocks`) (1 Endpoint + Peer Query Mode - Module 3)
| # | HTTP Method | Endpoint URL | Description | Access Level |
|---|---|---|---|---|
| 10d | `GET` | `/api/stocks/{ticker}/fundamental` | Comprehensive fundamental financial analysis across 7 core features | Public |
| 10e | `GET` | `/api/stocks/{ticker}/fundamental?peer={peer}` | Fundamental analysis with competitive peer benchmarking & narrative | Public |

### 6. Dashboard, Watchlist & Research Workspace (`/api/dashboard`) (9 Endpoints)
| # | HTTP Method | Endpoint URL | Description | Access Level |
|---|---|---|---|---|
| 11 | `GET` | `/api/dashboard/watchlist` | Get user's saved watchlist enriched with live pricing & currencies | Authenticated |
| 12 | `POST` | `/api/dashboard/watchlist` | Save stock to watchlist (enforces `UNIQUE(user_id, ticker)`) | Authenticated |
| 13 | `DELETE`| `/api/dashboard/watchlist/{id}` | Remove a stock from the authenticated user's watchlist | Authenticated |
| 14 | `POST` | `/api/dashboard/research` | Launch multi-agent research task and generate report | Authenticated |
| 15 | `GET` | `/api/dashboard/recent-research` | Retrieve past research tasks and status history | Authenticated |
| 16 | `GET` | `/api/dashboard/research/{id}/report` | Retrieve generated report (synthesis, fundamentals, limitations) | Authenticated |
| 16a| `DELETE`| `/api/dashboard/research/{id}` | Delete an individual research report and associated task records | Authenticated |
| 17 | `GET` | `/api/dashboard/preferences` | Load user's default market exchange and horizon | Authenticated |
| 18 | `PUT` | `/api/dashboard/preferences` | Update and persist user preferences in database | Authenticated |

> **Endpoint Summary:** **23 Unique Endpoints** (12 Public, 11 Protected by JWT Cookie Guard) — tested across **27 requests** in Postman.  
> **Automated API Testing:** All endpoints are verified in Postman and automated Python test suites.

---

## 15. Automated Testing Suite (Modules 1, 2 & 3)

The project includes 3 standalone automated integration verification suites:

### 1. Module 1: Core E2E & Authentication Suite (`test_e2e_full.py`):
```bash
python test_e2e_full.py
```
- Verifies health check, registration complexity, duplicate handling, login credential checks, JWT issuance, profile retrieval, watchlist CRUD, and research task logging.

### 2. Module 2: Market Analytics & Time Series Engine (`test_module_2.py`):
```bash
python test_module_2.py
```
- Verifies historical OHLCV data collection, TSA momentum indicators (SMA 20, SMA 50), volatility, 10-bin return histogram, company profile, financial statements, and research report generation.

### 3. Module 3: Fundamental Analysis Agent Verification Suite (`test_module_3.py`):
```bash
python test_module_3.py
```
```
===========================================================================
MODULE 3 VERIFICATION SUITE: FUNDAMENTAL ANALYSIS AGENT & RATIOS ENGINE
Features: Revenue/Earnings, Profitability, Debt/Stability, Ratios (P/E, P/B, ROE),
          Historical Performance, Peer Benchmarking, Data Audit Notice
===========================================================================

[TEST 1] Testing GET /api/stocks/INFY.NS/fundamental ...
  --> [PASS] Company Profile: Price=Rs.1162.4, Market Cap=Rs.470,856.24 Cr, 52W Range=980.4 - 1728.0.

[TEST 2] Verifying Feature 1: Revenue and Earnings Trajectory ...
  --> [PASS] Feature 1 Verified: YoY Growth=4.57%, Multi-Year Statements Count=4 years.

[TEST 3] Verifying Feature 2: Profitability Margins (Operating, Net, ROE, ROA) ...
  --> [PASS] Feature 2 Verified: Operating Margin=25.32%, Net Margin=16.44%, ROE=33.85%, ROA=20.14%.

[TEST 4] Verifying Feature 3: Debt & Financial Stability (Debt/Equity, Current Ratio) ...
  --> [PASS] Feature 3 Verified: Debt-to-Equity=0.1, Current Ratio=1.98x (Low Debt Leverage / Safe Solvency).

[TEST 5] Verifying Feature 4: Financial Ratios (P/E, P/B, EPS) ...
  --> [PASS] Feature 4 Verified: P/E Ratio=15.12x, P/B Ratio=4.83x, EPS=76.91.

[TEST 6] Verifying Feature 5: Historical Financial Statements Breakdown & YoY ...
  --> [PASS] Feature 5 Verified: 3 historical performance milestones tracked.

[TEST 7] Verifying Feature 6: Peer Benchmarking (INFY.NS vs AAPL) ...
  --> [PASS] Feature 6 Verified: Selected Peer='AAPL', Table Rows=5, Narrative Length=566 chars.

[TEST 8] Verifying Feature 7: Data Audit Notice & Missing Disclosures ...
  --> [PASS] Feature 7 Verified: Data Audit Notice: 'We retrieved all available information from official filings, but unfortunately ...'.

[TEST 9] Verifying Fundamental Analysis for US Equity (AAPL vs MSFT) ...
  --> [PASS] US Equity Verified: Ticker='AAPL', Currency='USD', Peer='MSFT'.

===========================================================================
ALL MODULE 3 AUTOMATED INTEGRATION TESTS PASSED SUCCESSFULLY! (100%)
===========================================================================
```

---

## 16. License & Acknowledgments

This project was developed as part of the **Infosys Springboard Virtual Internship 7.0 (Batch 5)** under the project track **AI-Powered Multi Agent System for Market Analysis and Research**.
