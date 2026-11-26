# AI-Powered Multi-Agent System for Market Analysis and Research (EquityLens)

A full-stack stock market analysis app. Users register and log in, search NSE/BSE stocks, view live quotes, price history charts, company profiles, fundamentals and financial statements, and manage a personal watchlist and preferences.

> **Status:** Milestone 1 (data layer, authentication, dashboard) complete. Week 3: Fundamental Analysis Agent added.

## Features

- User registration and login (JWT in an httpOnly cookie)
- Stock search with NSE / BSE market support
- Quote, price history, profile, financials and statements (annual / quarterly)
- Interactive charts (Plotly)
- Watchlist, preferences and profile panel
- Data integrity checks on provider data (missing columns, short history)
- Short in-memory cache to avoid hitting the data provider repeatedly
- **Fundamental Analysis Agent** (Week 3): revenue, profitability and debt analysis, P/E, P/B and ROE, historical and peer comparison, missing-data detection

## Tech Stack

| Layer    | Tools |
|----------|-------|
| Frontend | React 18, Vite, React Router, Plotly |
| Backend  | FastAPI, SQLAlchemy-style models, pandas, yfinance (Yahoo Finance) |
| Database | SQLite (`app.db`, created locally) |
| Testing  | pytest (27 tests) |

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── agents/         # fundamental.py (Fundamental Analysis Agent)
│   │   ├── routers/        # API routes (auth, market, ...)
│   │   └── services/       # market data, ticker helpers
│   ├── tests/
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/     # incl. FundamentalCard.jsx
│   │   └── pages/          # Login, Register, Dashboard
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── LICENSE
```

## Local URLs

| Service  | URL |
|----------|-----|
| Frontend (Dashboard) | http://localhost:5173/dashboard#dashboard |
| Backend API | http://127.0.0.1:8000 |

## Getting Started

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

Create a `.env` file inside `backend/` (never commit it) with your secrets, for example:

```
SECRET_KEY=your-secret-key
```

Run the server:

```bash
uvicorn app.main:app --reload
```

Backend runs at **http://127.0.0.1:8000** (interactive API docs at http://127.0.0.1:8000/docs).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173**, and the dashboard is at **http://localhost:5173/dashboard#dashboard**. To point at a different backend, set `VITE_API_URL` in `frontend/.env`.

### 3. Tests

```bash
cd backend
pytest
```

All 27 tests pass.

## API Overview (market)

All routes need a logged-in user.

| Method | Endpoint                         | Description |
|--------|----------------------------------|-------------|
| GET    | `/market/{ticker}/history`       | OHLCV history (`period`: 1mo, 3mo, 6mo, 1y, 5y) |
| GET    | `/market/{ticker}/quote`         | Latest quote with 52-week range |
| GET    | `/market/{ticker}/profile`       | Company profile |
| GET    | `/market/{ticker}/financials`    | Key financial metrics |
| GET    | `/market/{ticker}/statements`    | Statements (`frequency`: annual / quarterly) |
| GET    | `/market/{ticker}/fundamental`   | Fundamental analysis report (optional peer tickers) |

Query param `market` accepts `NSE` (default) or `BSE`.

## Week 3: Fundamental Analysis Agent

The agent analyses a company's financial performance and condition from its annual statements (Yahoo Finance via yfinance).

- **Revenue and earnings:** growth, 3-year CAGR, net income trend
- **Profitability:** gross, operating and net margin, ROE, ROA
- **Debt and stability:** debt-to-equity, net debt, current ratio, interest coverage, free cash flow
- **Valuation:** P/E, P/B and ROE, shown next to the provider's own figures for comparison
- **Historical comparison:** last 4 fiscal years
- **Peer comparison:** up to 4 peers, with peer median and above/below position
- **Data quality:** missing or inconsistent data detection with a data-confidence rating

Code: `backend/app/agents/fundamental.py`, tests in `backend/tests/test_fundamental.py`, UI in `frontend/src/components/FundamentalCard.jsx`.

*This is an analysis aid, not investment advice.*

## Notes

- `.env`, `venv/`, `node_modules/`, `dist/` and `*.db` are git-ignored.
- Market data comes from Yahoo Finance via `yfinance`; availability can vary.

## License

See the [LICENSE](LICENSE) file.