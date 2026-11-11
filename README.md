# Multi-Agent Stock Research Analyst Platform (Module 1)

A production-grade, secure, personalized stock research workspace built with **React (Vite + Tailwind CSS)**, **FastAPI (Python)**, **SQLAlchemy**, and **PostgreSQL**.

Module 1 establishes the foundational infrastructure, user authentication, personal portfolio watchlist, search across global exchanges (NSE, BSE, NASDAQ, NYSE), preference configuration, research execution lifecycle, and an extensible service interface ready for future multi-agent quantitative and LLM analysis pipelines.

---

## 1. System Architecture

```text
stock-research-platform/
│
├── frontend/                     # React 19 + Vite + Tailwind CSS Single-Page Application
│   ├── src/
│   │   ├── api/client.js         # Axios client with JWT interceptor & 401 handler
│   │   ├── components/           # Reusable UI components (Modals, Badges, Search)
│   │   ├── context/AuthContext   # Global Auth & Preferences state management
│   │   ├── layouts/AppLayout     # Main dashboard layout with responsive sidebar
│   │   ├── pages/                # Pages: Dashboard, History, Watchlist, Preferences, Profile
│   │   ├── App.jsx               # Protected & Public route switchboard
│   │   └── main.jsx
│   ├── tailwind.config.js
│   └── vite.config.js            # Reverse proxy configuration to FastAPI
│
├── backend/                      # FastAPI Python Application
│   ├── app/
│   │   ├── core/                 # Config, bcrypt hashing, JWT security, rate limiter
│   │   ├── database.py           # SQLAlchemy session and engine management
│   │   ├── models/               # SQLAlchemy models (User, Preferences, Watchlist, Tasks, Reports)
│   │   ├── schemas/              # Pydantic v2 validation models
│   │   ├── services/             # Stock data lookup & Multi-Agent Coordinator interface
│   │   ├── routers/              # Modular API endpoints (/auth, /users, /watchlist, /research, etc.)
│   │   └── main.py               # FastAPI entrypoint, CORS & error handlers
│   ├── alembic/                  # Database migration scripts & environments
│   ├── tests/                    # Automated pytest test suite
│   ├── requirements.txt
│   └── .env.example
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 2. Technology Stack

- **Frontend:**
  - React 19 & Vite 8
  - Tailwind CSS 3
  - React Router DOM 7
  - Axios HTTP client
  - Lucide React icon library
- **Backend:**
  - Python 3.11+
  - FastAPI & Uvicorn
  - SQLAlchemy 2.0 ORM
  - Pydantic v2
  - PostgreSQL with `psycopg2-binary`
  - Alembic for database migrations
  - Passlib & Bcrypt (12-round salted hashing)
  - Python-Jose (JWT HS256 tokens)
  - YFinance & HTTPX for market data lookup
- **Database:**
  - PostgreSQL 18

---

## 3. Database Schema

The database schema utilizes strict foreign keys, indexes, and unique constraints:

1. **`users`**:
   - `user_id` (PK, Serial)
   - `full_name` (VARCHAR)
   - `email` (VARCHAR, Unique, Indexed)
   - `password_hash` (VARCHAR)
   - `created_at`, `updated_at` (TIMESTAMPTZ)
2. **`user_preferences`**:
   - `preference_id` (PK, Serial)
   - `user_id` (FK -> `users.user_id`, Unique, Cascade)
   - `preferred_market` (VARCHAR: NSE, BSE, NASDAQ, NYSE)
   - `analysis_period` (VARCHAR: 1 Month, 3 Months, 6 Months, 1 Year, 5 Years)
   - `updated_at` (TIMESTAMPTZ)
3. **`saved_stocks`**:
   - `saved_stock_id` (PK, Serial)
   - `user_id` (FK -> `users.user_id`, Cascade)
   - `company_name`, `ticker`, `market`
   - `created_at` (TIMESTAMPTZ)
   - *Constraint:* `uq_user_ticker_market` (Unique per user, ticker, and exchange)
4. **`research_tasks`**:
   - `task_id` (PK, Serial)
   - `user_id` (FK -> `users.user_id`, Cascade)
   - `company_name`, `ticker`, `market`, `analysis_period`
   - `status` (`Pending`, `Processing`, `Completed`, `Failed`)
   - `error_message` (TEXT, Nullable)
   - `created_at`, `updated_at` (TIMESTAMPTZ)
5. **`research_reports`**:
   - `report_id` (PK, Serial)
   - `task_id` (FK -> `research_tasks.task_id`, Unique, Cascade)
   - `report_content` (TEXT / JSON)
   - `created_at` (TIMESTAMPTZ)

---

## 4. Getting Started & Installation

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL running locally or in Docker

### Step 1: Database Setup
Create the project database in PostgreSQL:
```bash
# In psql or your database management tool:
CREATE DATABASE stock_research_db;
```

### Step 2: Backend Setup
1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your `.env` file:
   ```bash
   cp .env.example .env
   ```
   Ensure `DATABASE_URL` matches your local PostgreSQL connection string:
   ```env
   DATABASE_URL=postgresql://postgres@localhost:5432/stock_research_db
   SECRET_KEY=9f83a45c829e5a1b32d4e78f01c4b2a95d7e3f1a6c8b0d2e4f6a8c0e2b4d6f8a
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ENVIRONMENT=development
   FRONTEND_URL=http://localhost:5173
   ```
5. Run database migrations with Alembic:
   ```bash
   alembic upgrade head
   ```
6. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The interactive Swagger documentation will be available at: [http://localhost:8000/api/docs](http://localhost:8000/api/docs).

---

### Step 3: Frontend Setup
1. Open a new terminal and navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open your browser at: [http://localhost:5173](http://localhost:5173).

---

## 5. Running Automated Backend Tests

The test suite thoroughly verifies registration validation, email uniqueness, password strength, authentication tokens, user data isolation, preferences, watchlist duplicates, and research task permissions.

Execute tests via:
```bash
cd backend
pytest tests -v
```

---

## 6. Multi-Agent Engine Integration Architecture

The platform is designed for seamless expansion into Module 2 (Multi-Agent Swarm Analysis). In `backend/app/services/research_engine.py`:

```python
class BaseResearchAgent(abc.ABC):
    @property
    @abc.abstractmethod
    def agent_name(self) -> str: ...

    @abc.abstractmethod
    async def analyze(self, ticker: str, market: str, period: str, market_data: Dict[str, Any]) -> Dict[str, Any]: ...

class MultiAgentResearchCoordinatorInterface(abc.ABC):
    @abc.abstractmethod
    def register_agent(self, agent: BaseResearchAgent) -> None: ...

    @abc.abstractmethod
    async def run_pipeline(self, task: ResearchTask) -> Dict[str, Any]: ...
```

When research is submitted:
1. `POST /api/research` creates a task in PostgreSQL with status `Pending`.
2. A background worker transitions status to `Processing`.
3. The coordinator runs data extraction and agent pipelines.
4. The output is persisted to `research_reports` in PostgreSQL and status transitions to `Completed`.
5. If any error occurs, the task transitions to `Failed` with an informative error message.
6. The frontend automatically tracks and reflects these state changes in real time.

---

## 7. Security Highlights

- **Bcrypt Hashing**: Salting and hashing with 12 rounds; plain-text passwords are never stored.
- **Strict Claims-Based Auth**: The user identity is always extracted from the verified JWT payload (`sub` claim) on the server. Frontend-supplied IDs are never trusted.
- **Multi-Tenant Isolation**: All queries for preferences, watchlist, research tasks, and reports filter strictly by `user_id == current_user.user_id`.
- **Brute-Force Rate Limiting**: Sliding-window rate limiter on `/api/auth/login` to prevent credential stuffing.
- **SQL Injection Defense**: All database queries utilize parameterized SQLAlchemy ORM statements.
- **CORS & HTTP-only Cookies**: Strict origin restrictions and secure cookie configuration.

