# ORIONNEX

A multi-agent stock research analyst. **Module 1: user authentication and research workspace.**

User authentication and a personal research workspace. Users can register, log in, keep a watchlist of stocks, choose their market and analysis period, and view their research history. Stock search is powered by Yahoo Finance (`yfinance`) and all user data is stored in PostgreSQL.

## Features

- **Home page** with Login and Register buttons
- **Registration** with email validation, password rules and bcrypt password hashing
- **Login** with JWT authentication (stored in an HTTP-only cookie)
- **Protected dashboard**: only logged-in users can open it
- **Watchlist**: search stocks by company name or ticker (yfinance), save and remove them
- **Preferences**: choose a market (NSE, BSE, NASDAQ, NYSE) and an analysis period (1 month to 5 years)
- **Research history**: every research task is saved per user with its market, period, date and status
- **Data isolation**: each user can only read and change their own data

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS, React Router |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL |
| Auth | JWT (PyJWT), bcrypt |
| Market data | yfinance |

## Project structure

```
stock-research/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app
│   │   ├── config.py          # reads .env
│   │   ├── database.py        # SQLAlchemy engine and session
│   │   ├── models.py          # users, user_preferences, saved_stocks, research_tasks
│   │   ├── schemas.py         # request/response validation
│   │   ├── security.py        # password hashing and JWT
│   │   ├── deps.py            # current-user and CSRF checks
│   │   ├── market.py          # yfinance search and ticker validation
│   │   └── routers/           # auth, preferences, watchlist, research
│   ├── init_db.py             # creates the database and tables
│   ├── schema.sql             # the same schema as plain SQL
│   ├── requirements.txt
│   └── .env.example
└── frontend/                  # React app
```

## Prerequisites

Install these first:

- **Python 3.10 or newer**: https://www.python.org/downloads/
- **Node.js 18 or newer (LTS)**: https://nodejs.org
- **PostgreSQL 14 or newer**: https://www.postgresql.org/download/ (remember the password you set for the `postgres` user)
- An internet connection (yfinance fetches data from Yahoo Finance)

## How to run

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd stock-research
```

### 2. Set up the backend

```bash
cd backend
pip install -r requirements.txt
```

Create your environment file by copying the example:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `backend/.env` and fill in your values:

```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_NAME=stock_research
SECRET_KEY=a-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=60
COOKIE_SECURE=false
```

| Variable | Meaning |
|---|---|
| `DB_PASSWORD` | The password you set when installing PostgreSQL. It can contain special characters. |
| `SECRET_KEY` | Signs the login tokens. Use any long random string and keep it private. |
| `COOKIE_SECURE` | Keep `false` for local development. Set `true` when deployed behind HTTPS. |

Create the database and tables (PostgreSQL must be running):

```bash
python init_db.py
```

You should see: `Tables ready: users, user_preferences, saved_stocks, research_tasks`

Start the backend:

```bash
python -m uvicorn app.main:app --reload
```

The API runs at http://localhost:8000 and its interactive documentation is at http://localhost:8000/docs. Keep this terminal open.

### 3. Set up the frontend

Open a **second terminal**:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser. The frontend forwards all `/api` requests to the backend on port 8000, so both must be running.

## Try it out

1. Open http://localhost:5173 and click **Register**. Create an account.
2. Log in with the same email and password. You are taken to the dashboard.
3. In the watchlist search, type a company such as `tcs` or `reliance`, then save it.
4. Change your market or analysis period in **Preferences** and save.
5. Click **Research** on a saved stock. A new row appears in your research history.
6. Log out, register a second account and confirm it cannot see the first account's data.

To inspect the database, open `psql` or pgAdmin, connect to `stock_research` and run `SELECT * FROM users;`. Passwords are stored only as bcrypt hashes.

## API overview

All routes start with `/api`. Routes other than register and login require a logged-in user.

| Method | Route | Purpose |
|---|---|---|
| POST | `/auth/register` | Create an account |
| POST | `/auth/login` | Log in and set the session cookie |
| POST | `/auth/logout` | Clear the session cookie |
| GET | `/auth/me` | Current user |
| GET / PUT | `/preferences` | Read or update market and analysis period |
| GET | `/stocks/search?q=&market=` | Search stocks through yfinance |
| GET / POST | `/watchlist` | List or add saved stocks |
| DELETE | `/watchlist/{id}` | Remove a saved stock |
| GET / POST | `/research` | List research history or start a research task |
| GET | `/research/{id}` | Open one research task |

## Security notes

- Passwords are hashed with bcrypt and never stored in plain text.
- The login token is stored in an HTTP-only cookie, so page scripts cannot read it.
- State-changing requests require an `X-Requested-With` header as CSRF protection.
- The user identity always comes from the verified token, never from the request body, so users cannot access each other's data.
- Never commit your `.env` file. It is already listed in `.gitignore`.
- For production, serve the app over HTTPS and set `COOKIE_SECURE=true`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `uvicorn is not recognized` (Windows) | Run it as `python -m uvicorn app.main:app --reload` |
| `connection refused` or `could not connect to server` | PostgreSQL is not running. Start the PostgreSQL service and try again. |
| `password authentication failed` | `DB_PASSWORD` in `backend/.env` does not match your PostgreSQL password. |
| `KeyError: 'SECRET_KEY'` | `backend/.env` is missing or has no `SECRET_KEY`. |
| Stock search returns nothing or an error | Run `pip install -U yfinance`. If you see "Too Many Requests", wait a few minutes. Some college or office networks block Yahoo Finance; try another network. |
| `npm` is not recognized | Install Node.js (LTS), then open a new terminal. |
| Frontend loads but every request fails | The backend is not running on port 8000. Start it first. |

## Current scope

This module covers authentication, the watchlist, preferences and research history. New research tasks are saved with the status **Pending**. The analysis agents that process tasks and write reports belong to a later module and will update the status and report fields that already exist in the database.
