# AlphaAgent: AI-Powered Multi-Agent Stock Research & Analysis Platform

> **Infosys Springboard Virtual Internship Project**  
> An autonomous, quantitative equity research workspace combining real-time market data, interactive risk metrics, technical indicators, and persistent user workspaces.

---

## 📌 Project Overview

**AlphaAgent** is a full-stack, enterprise-grade equity research platform designed to automate financial data gathering, quantitative modeling, risk auditing, and multi-exchange market tracking.

Built as part of the **Infosys Springboard Virtual Internship**, this repository hosts the complete implementation of **Module 1: User Authentication & Foundation Workspace**, fully connected to a **FastAPI** backend, a **PostgreSQL** relational database, and an interactive **React + Vite** frontend powered by live market feeds from **Yahoo Finance**.

---
<img width="1837" height="837" alt="Screenshot 2026-11-14 231137" src="https://github.com/user-attachments/assets/94f8b631-c554-4d22-bebc-97d361485403" />
<img width="1886" height="866" alt="Screenshot 2026-11-14 231254" src="https://github.com/user-attachments/assets/92ff8035-adac-415b-87fe-cf2e7ac5f507" />




## 🚀 Key Features Implemented (Module 1 Scope)

### 1. Enterprise User Authentication & Security
- **Bcrypt Password Hashing:** Secure one-way hashing with dynamic salt generation; plaintext passwords are never persisted.
- **Stateless JWT Authorization:** Issues signed JSON Web Tokens (`HS256`) stored in browser storage for authenticated sessions and route protection.
- **Strict 5-Point Password Complexity Enforcement:**
  - Minimum 8 characters.
  - At least one uppercase letter (`A-Z`).
  - At least one lowercase letter (`a-z`).
  - At least one numeric digit (`0-9`).
  - At least one special symbol (`!@#$%^&*`).
- **Interactive Password Strength Meter:** Visual real-time indicator (Weak, Moderate, Strong) with a dynamic criteria checklist.
- **✨ 1-Click "Suggest Strong Password" Generator:** Generates high-entropy 12-character cryptographic passwords and auto-fills both fields.

### 2. Official Google OAuth 2.0 Integration (Google Identity Services)
- Direct integration with Google Cloud Platform OAuth 2.0 client via Google Identity Services (`GSI`) SDK.
- **Authentic Account Picker:** Native Google popup showing accounts logged into the user's browser.
- **Strict Log In Verification (`/login`):** If an unregistered Google email is selected, it displays a clear `"Account Not Found"` warning and routes the user to create an account.
- **Instant Registration (`/register`):** Signing in on the registration page automatically provisions a PostgreSQL user record, seeds default preferences, and enters the dashboard.

### 3. Persistent PostgreSQL Relational Architecture
Normalized schema with 7 dedicated relational tables:
1. `users` — Primary user credentials and identities.
2. `user_preferences` — User-specific default market and analysis period preferences.
3. `saved_stocks` — User-curated watchlist with exchange mapping.
4. `research_tasks` — User research task tracking and status history.
5. `agent_results` — Multi-agent quantitative outputs (Module 2+ foundation).
6. `source_documents` — Financial filings and data source citations.
7. `research_reports` — Compiled multi-agent equity dossiers.

### 4. Real-Time Market Data Engine (Yahoo Finance)
- **Multi-Exchange Compatibility:** Automatic ticker normalization:
  - **NSE (India):** Suffixes `.NS` (e.g. `RELIANCE.NS`, `INFY.NS`).
  - **BSE (India):** Suffixes `.BO` (e.g. `TCS.BO`).
  - **NASDAQ & NYSE (US):** Direct global ticker routing (e.g. `AAPL`, `MSFT`, `JPM`).
- **Live Fundamental Ratios:** Real-time extraction of Trailing P/E, Price-to-Book (P/B), Return on Equity (ROE), Debt-to-Equity, Market Capitalization, and 52-Week Range.
- **Live Index Ticker Tape:** Real-time top navigation bar displaying live values for NIFTY 50, SENSEX, NASDAQ, S&P 500, Brent Crude, and Gold.

### 5. Dynamic Timeframe Analytics & Quantitative Modeling
Unlike static platforms, changing the analysis timeframe (**1 Month, 3 Months, 6 Months, 1 Year, 5 Years**) recalculates every quantitative signal in real-time:
- **Technical Signals:** SMA 50, SMA 200, RSI (14-period), MACD (12, 26, 9), and Annualized Volatility.
- **Dynamic Risk Metrics:**
  - **Maximum Drawdown:** Calculated peak-to-trough drop over the requested timeframe.
  - **Horizon Return:** Exact percentage capital gain/loss over the selected window.
  - **Adaptive Period High/Low:** Top ribbon card dynamically switches between `1 Month High/Low` and `52W High/Low`.

### 6. Real-Time Financial News Intelligence
- Streaming real-time headlines directly from Yahoo Finance API for the currently inspected stock.
- Displays news publisher, publication time, and direct verified external source links.

### 7. Interactive Watchlist & Research Task History
- Add any stock symbol across NSE, BSE, NASDAQ, or NYSE with live quote validation.
- Remove stocks with instant PostgreSQL database sync.
- "Run Agent Research" initiates an equity audit task logged to the database.

---

## 🏗️ Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Backend Framework** | Python 3.10+, FastAPI (Asynchronous REST API) |
| **Database & ORM** | PostgreSQL 18, SQLAlchemy 2.0, Psycopg2-binary |
| **Security & Auth** | Passlib, Bcrypt, Python-Jose (JWT), Google Identity Services |
| **Financial Data & Math** | Yahoo Finance (`yfinance`), Pandas, NumPy |
| **Frontend Framework** | React 19, Vite 6, Tailwind CSS v4 |
| **Icons & UI** | Lucide React |

---

## 📁 Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── auth.py              # JWT tokens, password hashing & dependencies
│   │   ├── config.py            # Environment configuration settings
│   │   ├── database.py          # SQLAlchemy engine & session maker
│   │   ├── main.py              # FastAPI application entrypoint & CORS
│   │   ├── models.py            # SQLAlchemy PostgreSQL database models (7 tables)
│   │   ├── schemas.py           # Pydantic v2 validation schemas
│   │   ├── routers/
│   │   │   ├── auth.py          # /api/auth (Register, Login, Google OAuth, Profile)
│   │   │   ├── market.py        # /api/market (Live quotes, history, technical analysis)
│   │   │   ├── preferences.py   # /api/preferences (User market & timeframe preferences)
│   │   │   ├── research.py      # /api/research (Research tasks & history audit log)
│   │   │   └── watchlist.py     # /api/watchlist (CRUD user saved stocks)
│   │   └── services/
│   │       └── market_data.py   # Yahoo Finance service & quantitative calculations
│   ├── .env.example             # Backend environment template
│   └── requirements.txt         # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── Navbar.jsx       # Navigation bar with live ticker tape & theme toggle
│   │   ├── context/
│   │   │   ├── AuthContext.jsx  # Authentication session state provider
│   │   │   └── ThemeContext.jsx # Dark / Light mode state provider
│   │   ├── pages/
│   │   │   ├── Home.jsx         # Landing page with live market preview
│   │   │   ├── Login.jsx        # Log In page with Google GIS One-Tap & validation
│   │   │   ├── Register.jsx     # Create Account with strong password generator
│   │   │   └── Dashboard.jsx    # Primary research workspace & multi-agent analytics
│   │   ├── services/
│   │   │   └── api.js           # Axios API service client
│   │   ├── App.jsx              # Application routing & layout
│   │   └── main.jsx             # React entrypoint
│   ├── .env.example             # Frontend environment template
│   ├── index.html               # Google Identity Services SDK include
│   ├── package.json             # Frontend NPM dependencies
│   └── vite.config.js           # Vite build configuration
├── .gitignore                   # Git exclusions (node_modules, .env, __pycache__)
├── requirements.txt             # Root Python dependencies
└── README.md                    # Project documentation
```

---

## ⚙️ Step-by-Step Installation & Run Guide

### 1. Prerequisites
Ensure you have the following installed on your machine:
- **Python 3.10+**: [python.org](https://www.python.org/)
- **Node.js 18+ and npm**: [nodejs.org](https://nodejs.org/)
- **PostgreSQL 15+**: [postgresql.org](https://www.postgresql.org/) (Running on port `5432`)
- **Git**: [git-scm.com](https://git-scm.com/)

---

### 2. Clone the Repository
```bash
git clone <YOUR_REPOSITORY_URL>
cd <REPOSITORY_FOLDER>
```

---

### 3. Database Setup (PostgreSQL)
Open your PostgreSQL terminal (`psql`) or pgAdmin and create the database:
```sql
CREATE DATABASE stock_research_db;
```
*(The FastAPI backend automatically initializes all 7 tables upon first startup).*

---

### 4. Backend Setup & Run

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. (Optional but recommended) Create and activate a Python virtual environment:
   ```bash
   # On Windows:
   python -m venv .venv
   .venv\Scripts\activate

   # On macOS / Linux:
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Copy the example environment file and customize your database password:
   ```bash
   cp .env.example .env
   ```
   Open `backend/.env` and verify your connection string:
   ```env
   DATABASE_URL=postgresql://postgres:<YOUR_PASSWORD>@localhost:5432/stock_research_db
   SECRET_KEY=infosys_stock_research_super_secret_key_2026
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_google_client_secret_here
   ```

5. Start the FastAPI development server:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   *FastAPI server will be running at:* `http://127.0.0.1:8000`  
   *Interactive Swagger Documentation:* `http://127.0.0.1:8000/docs`

---

### 5. Frontend Setup & Run

1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Configure frontend environment variables:
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Ensure `frontend/.env` contains your Google Client ID:
   ```env
   VITE_GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
   ```

4. Start the Vite React development server:
   ```bash
   npm run dev
   ```
   *Frontend application will be accessible at:* `http://localhost:5173`

---

## 🌐 API Endpoints Reference

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/auth/register` | Register a new user with strong password validation | No |
| `POST` | `/api/auth/login` | Authenticate with email/password and obtain JWT token | No |
| `POST` | `/api/auth/google` | Official Google OAuth authentication (`login` / `register`) | No |
| `GET` | `/api/auth/me` | Fetch currently logged-in user profile | **Yes (JWT)** |
| `GET` | `/api/preferences` | Retrieve user market & timeframe preferences | **Yes (JWT)** |
| `PUT` | `/api/preferences` | Update user market & timeframe preferences | **Yes (JWT)** |
| `GET` | `/api/watchlist` | Retrieve user saved stocks with live quote enrichment | **Yes (JWT)** |
| `POST` | `/api/watchlist` | Add a stock ticker to user personal watchlist | **Yes (JWT)** |
| `DELETE` | `/api/watchlist/{ticker}` | Delete a stock ticker from user personal watchlist | **Yes (JWT)** |
| `GET` | `/api/market/quote/{ticker}` | Fetch real-time live price and valuation ratios from Yahoo Finance | No |
| `GET` | `/api/market/analysis/{ticker}` | Fetch dynamic technical indicators, risk metrics, and live news | No |
| `GET` | `/api/market/history/{ticker}` | Fetch historical OHLCV candlestick data for charting | No |
| `GET` | `/api/market/tape` | Fetch live indices for top ticker tape | No |
| `GET` | `/api/research/history` | Retrieve user research tasks audit log | **Yes (JWT)** |
| `POST` | `/api/research/start` | Launch and record an equity research task | **Yes (JWT)** |

---

## 🧪 Testing and Verification Checklist

1. **User Sign Up:**
   - Navigate to `http://localhost:5173/register`.
   - Test typing a simple password (e.g. `123456`) — observe the real-time checklist and error prevention.
   - Click **"Suggest Strong Password"** — notice the 12-character high-security auto-fill.
   - Complete registration and verify redirection.
2. **Google OAuth Flow:**
   - Attempt to log in with an unregistered Google account on `/login` — notice the friendly `"Account Not Found"` banner and prompt to register.
   - Use Google Sign-In on `/register` — experience 1-click registration directly into the dashboard.
3. **Workspace Reactivity:**
   - Change the timeframe from **"1 Month"** to **"1 Year"** — observe the dynamic High/Low range card and technical indicators change in real-time.
   - Switch exchange from **"NSE"** to **"NASDAQ"** — observe instant currency and benchmark symbol adaptation.
4. **Watchlist CRUD:**
   - Search and add a ticker (e.g. `TCS`, `NVDA`).
   - Remove a stock and refresh the page to verify PostgreSQL persistence.

---

## 👩‍💻 Author & Acknowledgements

- **Student:** M. Vaishnavi
- **Mentorship & Program:** Infosys Springboard Virtual Internship
- **Project Domain:** AI-Powered Multi-Agent Stock Research and Analysis

