# AI-Powered Multi-Agent System for Market Analysis and Research (EquityLens)

A full-stack stock market analysis app. Users register and log in, search NSE/BSE stocks, view live quotes, price history charts, company profiles, fundamentals and financial statements, and manage a personal watchlist and preferences.

> **Status:** Milestone 1 (data layer, authentication, dashboard)

## Features

- User registration and login (JWT in an httpOnly cookie)
- Stock search with NSE / BSE market support
- Quote, price history, profile, financials and statements (annual / quarterly)
- Interactive charts (Plotly)
- Watchlist, preferences and profile panel
- Data integrity checks on provider data (missing columns, short history)
- Short in-memory cache to avoid hitting the data provider repeatedly

## Tech Stack

| Layer    | Tools |
|----------|-------|
| Frontend | React 18, Vite, React Router, Plotly |
| Backend  | FastAPI, SQLAlchemy-style models, pandas, yfinance (Yahoo Finance) |
| Database | SQLite (`app.db`, created locally) |
| Testing  | pytest |

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── routers/        # API routes (auth, market, ...)
│   │   └── services/       # market data, ticker helpers
│   ├── tests/
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   └── pages/          # Login, Register, Dashboard
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── LICENSE
```

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

API runs at `http://localhost:8000` (interactive docs at `/docs`).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:5173`. To point at a different backend, set `VITE_API_URL` in `frontend/.env`.

### 3. Tests

```bash
cd backend
pytest
```

## API Overview (market)

All routes need a logged-in user.

| Method | Endpoint                         | Description |
|--------|----------------------------------|-------------|
| GET    | `/market/{ticker}/history`       | OHLCV history (`period`: 1mo, 3mo, 6mo, 1y, 5y) |
| GET    | `/market/{ticker}/quote`         | Latest quote with 52-week range |
| GET    | `/market/{ticker}/profile`       | Company profile |
| GET    | `/market/{ticker}/financials`    | Key financial metrics |
| GET    | `/market/{ticker}/statements`    | Statements (`frequency`: annual / quarterly) |

Query param `market` accepts `NSE` (default) or `BSE`.

## Notes

- `.env`, `venv/`, `node_modules/`, `dist/` and `*.db` are git-ignored.
- Market data comes from Yahoo Finance via `yfinance`; availability can vary.

## License

See the [LICENSE](LICENSE) file.