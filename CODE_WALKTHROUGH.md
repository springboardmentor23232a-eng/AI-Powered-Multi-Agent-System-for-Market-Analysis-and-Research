# Understanding the Stock Research Analyst Module 1 code

This note explains the main request flow in plain language. It is intended to help you understand, test, and present the implementation.

## How a request moves through the app

1. A person uses a form or button in the React frontend.
2. `frontend/src/api.js` sends the request to FastAPI and includes browser cookies.
3. FastAPI validates the incoming data with the Pydantic classes in `backend/app/schemas.py`.
4. Protected routes use `backend/app/dependencies.py` to verify the session JWT and identify the signed-in user.
5. The route reads or changes records through SQLAlchemy models in `backend/app/models.py`.
6. PostgreSQL stores the data, and FastAPI returns a response for React to display.

## Backend files

- `config.py`: reads environment variables such as the database URL, cookie settings, and Google OAuth credentials.
- `database.py`: creates the SQLAlchemy engine and provides a database session to API routes.
- `models.py`: describes the seven PostgreSQL tables and their relationships.
- `schemas.py`: validates request bodies and shapes API responses.
- `security.py`: hashes and verifies passwords, creates JWTs, and prepares authentication cookies.
- `dependencies.py`: checks the signed-in user and protects cookie-based write requests against CSRF.
- `oauth.py`: configures the Google OpenID Connect client.
- `routers/auth.py`: handles registration, email/password login, Google login, current-session lookup, and logout.
- `routers/workspace.py`: handles preferences, stock search, watchlists, research tasks, and report retrieval.
- `main.py`: creates the FastAPI application, configures middleware, and registers the route groups.

## Frontend files

- `src/App.jsx`: renders the registration/login screens and the signed-in workspace.
- `src/api.js`: keeps HTTP calls in one place so components do not repeat request details.
- `src/main.jsx`: mounts the React application.
- `src/styles.css`: contains the responsive page styling.

## Why the user ID is not sent by the browser

A browser can be modified by its user, so the backend must not trust a `user_id` field supplied by the frontend. The protected route reads the user ID from the verified JWT instead. That is how watchlists, preferences, and research history stay associated with the correct account.

## What the research-history feature does today

Creating a research task saves a row with `Pending` status. The tables for reports, agent results, and source documents are ready to store later work, but this Module 1 app does not run the multi-agent analysis engine. A later module must process a task and update its status before a completed report can be shown.

## Database setup note

If all seven tables already exist in your Neon or Supabase PostgreSQL database, do not run `create_tables.py` again. Point `backend/.env` at that same database. The startup `create_all()` call is safe for existing tables, but it is not a schema migration tool.

## Before presenting the project

Try the registration, login, logout, Google login (if configured), preference saving, stock lookup, watchlist, and research-task flow yourself. Be ready to explain how password hashing, JWT verification, CSRF checks, foreign keys, and user-specific queries work.
