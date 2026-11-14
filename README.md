# Multi-Agent Stock Research Analyst
## Module 1: User Authentication and Research Workspace

> **Student Implementation Guide - Module 1 Completion**  
> Branch: `deepikapulluri`  
> Repository: `springboardmentor23232a-eng/AI-Powered-Multi-Agent-System-for-Market-Analysis-and-Research`

---

## 📌 Project Overview

This project delivers **Module 1: User Authentication and Research Workspace** of the **Multi-Agent Stock Research Analyst** platform. The system provides a secure, production-grade full-stack architecture featuring user registration, JWT-based login, personalized research workspace, watchlist management with ticker search, user preferences (Market & Analysis Period), and research task history with realistic multi-agent research report viewing.

---

## ✨ Key Features Implemented

### 1. User Registration
- Form fields: **Full Name**, **Email Address**, **Password**, and **Confirm Password**.
- Client-side and server-side validation for email formatting and password matching.
- Duplicate email prevention returning clear HTTP 400 error responses.
- Passwords hashed using industry-standard **bcrypt** (salt rounds = 12).
- Default user preferences (NASDAQ, 1 Year) auto-initialized upon registration.

### 2. User Login & JWT Authentication
- Email and password verification against stored bcrypt hash.
- Generates cryptographically signed **JSON Web Tokens (JWT)** with 24-hour expiration.
- Frontend includes the token in the `Authorization: Bearer <token>` header on all protected requests.
- Backend FastAPI dependency `get_current_user` strictly derives user identity from the verified token—never trusting user-supplied client parameters.
- Protected endpoints reject unauthenticated or expired requests with HTTP 401 Unauthorized.

### 3. User-Specific Research History
- Displays user's research tasks with:
  - **Company Name & Stock Ticker** (e.g. AAPL, TSLA, NVDA, RELIANCE, TCS)
  - **Market / Exchange** (NSE, BSE, NASDAQ, NYSE)
  - **Analysis Period** (1 Month, 3 Months, 6 Months, 1 Year, 5 Years)
  - **Research Date & Time**
  - **Status Badge** (Pending, Processing, Completed, Failed)
  - **View Report** action button.
- Tasks are strictly scoped to the authenticated user's ID.

### 4. Saved Stocks and Watchlists
- Real-time stock search with autocompletion across US and Indian equities.
- **Add to Watchlist** action with strict duplicate prevention per user.
- View all saved stocks with creation timestamp and exchange tags.
- **Remove from Watchlist** action.
- Direct **"Research"** quick action from any watchlist item to launch an analysis task.

### 5. User Preferences: Market and Analysis Period
- **Market Preferences**:
  - `NSE` – National Stock Exchange of India
  - `BSE` – BSE Ltd., India
  - `NASDAQ` – US Tech & Growth Equities
  - `NYSE` – New York Stock Exchange
- **Analysis Periods**:
  - `1 Month`, `3 Months`, `6 Months`, `1 Year`, `5 Years`
- Preferences persist in the database and automatically pre-fill new research workflows.

### 6. Realistic Multi-Agent Research Synthesis Engine
- Simulates realistic quantitative and fundamental research synthesis across 3 autonomous agents:
  1. **Fundamental Valuation Agent**: P/E ratios, Forward P/E, Revenue Growth, Operating Margin, ROE, and DCF Intrinsic Fair Value.
  2. **Technical Momentum Agent**: RSI (14), 50-day SMA, 200-day SMA, MACD crossover, Support & Resistance levels.
  3. **Market Sentiment & Macro Agent**: Sentiment score, macro monetary context, institutional catalysts, and downside risks.
  4. **Executive Recommendation**: Target price, projected upside percentage, and rating (e.g. `STRONG BUY`, `ACCUMULATE / OVERWEIGHT`).
- Interactive modal report viewer with print/export capabilities.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React.js (Vite), Lucide-React icons, Modern Institutional Dark UI CSS |
| **Backend** | FastAPI, Uvicorn, Python 3.13 |
| **Database** | SQLAlchemy ORM, SQLite (default zero-config) & PostgreSQL compatible |
| **Security** | PyJWT (HS256), bcrypt password hashing |
| **Data Validation** | Pydantic v2, Pydantic-Settings |
| **Testing** | Pytest, HTTPX TestClient |

---

## 🚀 How to Run Locally

### 1. Backend Setup & Run

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the backend API server
python run_backend.py
```

The FastAPI backend will start at:
- **API Server**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

*(Optional)* To use PostgreSQL instead of SQLite, set the `DATABASE_URL` environment variable:
```bash
set DATABASE_URL=postgresql://user:password@localhost:5432/stock_db
```

### 2. Frontend Setup & Run

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install dependencies (if not already installed)
npm install

# Start development server
npm run dev
```

The frontend will start at: `http://localhost:5173`.

### 3. Run Automated Tests

The test suite validates all Module 1 requirements (Registration, Login, Duplicate Checks, Auth Guards, Preferences, Watchlist, and Research Tasks):

```bash
cd backend
python -m pytest tests/ -v
```

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI entry point & CORS configuration
│   │   ├── config.py              # Application settings & JWT configuration
│   │   ├── database.py            # SQLAlchemy engine & session factory
│   │   ├── models.py              # User, UserPreference, SavedStock, ResearchTask
│   │   ├── schemas.py             # Pydantic v2 request/response schemas
│   │   ├── security.py            # Bcrypt hashing & PyJWT token utilities
│   │   ├── auth.py                # get_current_user JWT dependency
│   │   ├── mock_data.py           # Validated stock directory & ticker lookup
│   │   ├── research_engine.py     # Multi-agent synthesis report generator
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth_routes.py         # /api/auth (register, login, me)
│   │       ├── preferences_routes.py  # /api/preferences (get, update)
│   │       ├── watchlist_routes.py    # /api/watchlist (search, add, list, delete)
│   │       └── research_routes.py     # /api/research (tasks, reports)
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_module1.py        # Comprehensive Pytest test suite (100% pass)
│   ├── requirements.txt
│   └── run_backend.py
├── frontend/
│   ├── src/
│   │   ├── context/
│   │   │   └── AuthContext.jsx    # React Auth & session context
│   │   ├── services/
│   │   │   └── api.js             # API service with JWT Bearer interceptor
│   │   ├── components/
│   │   │   ├── Navbar.jsx         # Header with live market badges & user profile
│   │   │   ├── AuthModal.jsx      # Registration & Login tabbed modal
│   │   │   ├── PreferencesModal.jsx # Market & Period preferences selector
│   │   │   ├── WatchlistSection.jsx # Search autocomplete & saved stocks table
│   │   │   ├── ResearchHistorySection.jsx # User research tasks & status badges
│   │   │   ├── ReportModal.jsx    # Institutional multi-agent report viewer
│   │   │   └── NewResearchModal.jsx # Launch research task modal
│   │   ├── App.jsx                # Main layout & dashboard views
│   │   ├── App.css                # Institutional dark-theme styling
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── .gitignore
└── README.md
```

---

## 🔒 Security Best Practices Implemented
- **Password Safety**: Cleartext passwords are never persisted. Bcrypt hashes with automatic salts are enforced.
- **JWT Integrity**: Tokens are signed using HMAC-SHA256 with expiration checks.
- **Access Control**: Users can only read and mutate their own saved stocks, preferences, and research tasks. Client-provided user IDs are rejected in favor of verified claims from the JWT.
- **Input Sanitization**: Pydantic v2 enforces schema validation, regex email rules, and strict uppercase ticker normalization.
