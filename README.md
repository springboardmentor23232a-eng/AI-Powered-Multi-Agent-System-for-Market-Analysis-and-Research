# Stock Research Analyst — Module 1: Authentication & Research Workspace

This project implements the features described in the supplied **Module 1: User Authentication and Research Workspace** guide.

## Included features

- Email/password registration and login
- Google sign-in using OpenID Connect (optional; configure Google credentials to enable it)
- Argon2 password hashing
- Signed JWT stored in an HttpOnly cookie
- CSRF protection for cookie-authenticated write requests
- Protected personal dashboard
- Stock lookup by company name or ticker using Yahoo Finance search
- User-specific watchlist with duplicate prevention
- Market and analysis-period preferences
- User-specific research task history
- Research report storage and protected report retrieval endpoints
- PostgreSQL persistence through SQLAlchemy

## Important scope note

The uploaded guide is **Module 1** of a larger multi-agent stock research project. This implementation completes the authentication and research-workspace features in that guide. It creates the database structures needed for reports, agent results and source documents, but it does not yet implement the later LangGraph research agents that fetch financial statements, calculate technical indicators, analyse news, or generate finished investment reports.

A research request created in this module is therefore saved with `Pending` status. It will remain pending until a later research-engine module updates the task and writes its report. The app does not invent analysis results.

## Technology

- Frontend: React 18 + Vite
- Backend: Python + FastAPI
- Database: PostgreSQL (Neon-compatible)
- ORM: SQLAlchemy 2
- Validation: Pydantic
- Password hashing: Argon2 through `pwdlib`
- Authentication: JWT in HttpOnly cookie
- Google login: Authlib / OpenID Connect

## 1. Requirements

- Python 3.11 recommended
- Node.js 18 or newer
- A PostgreSQL database. Neon works; no local PostgreSQL server is required.
- Google OAuth credentials only if you want Google sign-in.

## 2. Configure PostgreSQL (Neon)

Create a Neon project and database. In Neon, choose **Connect** and copy the pooled or direct connection URI.

The backend uses Psycopg 3. Set the URL prefix to `postgresql+psycopg://`.

Example:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

Use your real Neon username, password, host and database name. If your password contains URL-reserved characters, URL-encode those characters before placing it in the connection URL.

## 3. Backend setup (Windows PowerShell)

Open a terminal in the project folder:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `backend/.env` and configure:

```env
APP_NAME=Stock Research Analyst API
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
JWT_SECRET_KEY=PASTE_A_LONG_RANDOM_SECRET
SESSION_SECRET_KEY=PASTE_A_DIFFERENT_LONG_RANDOM_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_ORIGIN=http://localhost:5173
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

Generate two independent secrets from the backend terminal:

```powershell
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(48)); print('SESSION_SECRET_KEY=' + secrets.token_urlsafe(48))"
```

Copy the two generated values into `.env`. Do not commit `.env`, share it, or put secrets in frontend code.

### Google sign-in setup

In Google Cloud Console:

1. Configure the Google Auth Platform consent screen and add your account as a test user if the app is in Testing mode.
2. Create an OAuth Client ID with application type **Web application**.
3. Add this Authorized JavaScript origin:

   `http://localhost:5173`

4. Add this Authorized redirect URI:

   `http://localhost:8000/api/auth/google/callback`

5. Put the generated client ID and secret in `backend/.env`.

If you leave the Google credentials blank, email/password registration and login still work. The Google button will return a configuration error until credentials are supplied.

### Database tables are already created

If you have already created all seven tables in Neon or Supabase, you do **not** need to run `create_tables.py`. Keep the existing tables and make sure `DATABASE_URL` points to that same PostgreSQL database.

At startup, `Base.metadata.create_all()` checks the SQLAlchemy models and creates only tables that are missing. It does not delete existing records or update the columns of an existing table. If you later change a model's columns, use a database migration (for example, Alembic) rather than expecting `create_all()` to alter the table.

The optional `create_tables.py` script is only for a fresh database where the tables have not been created yet. Do not run it just to restart the application.

Start the API:

```powershell
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Interactive API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health

## 4. Frontend setup

Open a **second terminal** at the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open:

`http://localhost:5173`

If your API is not running at `http://127.0.0.1:8000`, create `frontend/.env` with:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Restart Vite after changing frontend environment variables.

## 5. Database tables

| Table | Purpose |
|---|---|
| `users` | Login identity, password hash and Google subject |
| `user_preferences` | One user's default market and analysis period |
| `saved_stocks` | User-owned watchlist entries; duplicate ticker/market per user is prevented |
| `research_tasks` | User-owned research requests and status |
| `research_reports` | Generated report content linked one-to-one to a task |
| `agent_results` | Individual agent outputs linked to a task |
| `source_documents` | Research sources linked to a task |

All user-owned records use foreign keys to `users`. Research reports, agent results and source documents reference `research_tasks`.

## 6. Main API routes

### Authentication

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create a local account |
| POST | `/api/auth/login` | Verify password and issue session cookies |
| GET | `/api/auth/google/login` | Start Google sign-in |
| GET | `/api/auth/google/callback` | Validate Google identity and issue app session |
| GET | `/api/auth/me` | Return the current signed-in user |
| POST | `/api/auth/logout` | Clear session cookies |

### Workspace

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/stocks/search?q=TCS&market=NSE` | Search stock symbols |
| GET | `/api/watchlist` | List current user's saved stocks |
| POST | `/api/watchlist` | Save a stock |
| DELETE | `/api/watchlist/{saved_stock_id}` | Remove a saved stock |
| GET | `/api/preferences` | Read user preferences |
| PUT | `/api/preferences` | Save market and period |
| GET | `/api/research-tasks` | List current user's research history |
| POST | `/api/research-tasks` | Create a pending research request |
| GET | `/api/research-tasks/{task_id}/report` | Read a report owned by the current user |

Protected routes derive the user ID from the verified JWT. They do not trust a `user_id` supplied by the browser.

## 7. Suggested test sequence

1. Start the backend and frontend.
2. Register using a name, email and password.
3. Sign in with the same credentials.
4. Refresh the browser; the session should still be active.
5. Sign out and sign in again.
6. If Google OAuth is configured, test Google sign-in.
7. Open Preferences, change the market and analysis period, then save.
8. Open Watchlist, search for a company and add a result.
9. Remove a saved stock and confirm it disappears.
10. From Research history, create a request from a saved stock.
11. Confirm the task appears with `Pending` status.
12. Use the API docs or Neon SQL editor to inspect the rows.

Useful SQL checks:

```sql
SELECT user_id, full_name, email, created_at FROM users;
SELECT * FROM user_preferences;
SELECT * FROM saved_stocks ORDER BY created_at DESC;
SELECT * FROM research_tasks ORDER BY created_at DESC;
SELECT * FROM research_reports;
SELECT * FROM agent_results;
SELECT * FROM source_documents;
```

## 8. Security and deployment notes

- Passwords are never stored in plaintext.
- JWTs contain the user ID and expiry, not the password or profile secrets.
- The access token is in an HttpOnly cookie.
- State-changing cookie-authenticated requests require a CSRF token header.
- Google identity is validated by the backend using OpenID Connect.
- Keep Google Client Secret and database credentials on the backend only.
- For production, deploy behind HTTPS, set `COOKIE_SECURE=true`, use the deployed frontend origin, and update the Google OAuth origin/redirect URI.
- Add rate limiting, email verification, password recovery, structured audit logging and Alembic migrations before production use.
- `create_all()` is convenient for this learning module; it does not alter existing table definitions. Use Alembic when evolving an existing production schema.

## 9. Learning note

This code is intentionally organized into small modules. Before submitting or presenting it, make sure you can explain the request flow, password hashing, JWT verification, foreign keys, user-specific queries, and the reason the browser never decides which user's data it can read.
