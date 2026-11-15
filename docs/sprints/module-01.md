# Sprint 1: Module 1 (User Authentication and Research Workspace)

**Sprint goal:** set up the project foundation (backend, frontend, full database schema) and let a user register, sign in and manage a personal workspace with preferences, a watchlist and research history.

**Status:** Done (sprint dates: week 1)

## Product backlog and task status

| ID | Story / task | Priority | Status |
|---|---|---|---|
| M1-01 | Repo structure, environment-variable config, `.gitignore`, `.env.example` | Must | Done |
| M1-02 | Database setup + Alembic migration for all 6 spec tables + `user_preferences` | Must | Done |
| M1-03 | Register with email and password (validated, unique, hashed) | Must | Done |
| M1-04 | Log in and receive a JWT; wrong credentials rejected | Must | Done |
| M1-05 | Protected endpoints reject missing, invalid or expired tokens | Must | Done |
| M1-06 | View and update preferences (market, analysis period) | Must | Done |
| M1-07 | Add, list and remove saved stocks; no duplicates; private per user | Must | Done |
| M1-08 | Research history (own tasks only, newest first, paginated) | Should | Done |
| M1-09 | React app: register, login, protected workspace connected to the backend | Must | Done |
| M1-10 | Backend tests (pytest) + frontend tests (Vitest) + production build | Must | Done |
| M1-11 | GitHub Actions CI workflow | Should | Done (runs once pushed to GitHub) |
| M1-12 | README.txt, architecture, schema, sprint and test documentation | Must | Done |

## Requirements review against the PDF

| PDF requirement | Where | Result |
|---|---|---|
| User registration and login | `/auth/register`, `/auth/login`, AuthPage | Met |
| JWT-based authentication | `core/security.py`, `api/deps.py` | Met |
| Secure password hashing | Argon2id (pwdlib) | Met |
| User-specific research history | `/research/history`, ResearchHistoryCard | Met. Empty until Module 7 creates tasks |
| Saved stocks and watchlists | `/watchlist`, WatchlistCard | Met. Format check only until Module 2 |
| User preferences: market and analysis period | `/users/me/preferences`, PreferencesCard | Met |
| Milestone 1: database schema finalized | Migration 0001, docs/database-schema.md | Met |
| Milestone 1: FastAPI backend initialized | backend/ | Met |
| Milestone 1: PostgreSQL or SQLite configured | `DATABASE_URL`, docker-compose.yml | Met |
| Milestone 1: React skeleton; frontend talks to backend | frontend/, browser test | Met |
| API keys and secrets only in environment variables | `.env.example`, `.gitignore` | Met |
| Milestone 1: stock search and historical prices | Module 2 | Planned for week 2 |

## Testing results

| Suite | Environment | Result |
|---|---|---|
| Backend pytest (85 tests) | SQLite in-memory, Python 3.13 | 85 passed |
| Backend pytest (85 tests) | PostgreSQL 16, Python 3.13 | 85 passed |
| Backend pytest from a fresh virtualenv using only requirements-dev.txt | SQLite | 85 passed |
| Migration upgrade / `alembic check` / downgrade | PostgreSQL 16 and SQLite | Passed |
| Frontend Vitest (15 tests) | jsdom, Node 22 | 15 passed |
| ESLint + `vite build` | Node 22 | No errors |
| Live API check with curl (every endpoint) | uvicorn + PostgreSQL 16 | Passed |
| Browser end-to-end (Chrome, Playwright) | vite dev server + uvicorn + PostgreSQL 16 | Passed |
| Mutation check (bugs planted on purpose to prove the tests catch them) | SQLite | Tests failed as expected, then code restored |
| Clean-copy rehearsal of the CI steps (only the 70 files Git will upload, fresh installs) | PostgreSQL 16 + SQLite, Node 22 | All steps passed |

The full test-case list with expected and actual results is in `docs/test-reports/module-01-test-report.md`.

## Bugs found and fixed during the sprint

| # | Bug | How found | Fix |
|---|---|---|---|
| 1 | Watchlist form fields stacked vertically (CSS `w-full` overrode `flex-1`) | Browser screenshot | Separate width-free `fieldBaseClass`. Re-verified in browser |
| 2 | Browser console 404 for missing favicon | Browser end-to-end run | Added `public/favicon.svg` |
| 3 | Frontend test acted before the preferences form had loaded (test timing bug) | Vitest failure | Test now waits for the form |
| 4 | Health check used the global DB engine, so tests could not point it at the test DB | Code review | Health check now uses the request's DB session |
| 5 | Watchlist limit check loaded every row just to count them | Code review | Replaced with a SQL `COUNT` query |
| 6 | PostgreSQL test runs left tables behind, so a later `alembic upgrade` on the same database failed with "users already exists" | Clean-copy CI rehearsal | Tests now drop their tables when finished. Re-verified: tests, then migrations, both pass |

## Known issues and limitations (honest list)

1. **Ticker existence is not verified yet.** Only the format is checked. Real lookup arrives with market data in Module 2.
2. **Research history is empty** until Module 7 creates research tasks. The endpoint, ownership rules and UI are tested with directly inserted tasks.
3. **No refresh tokens.** Users sign in again after 60 minutes (configurable with `ACCESS_TOKEN_EXPIRE_MINUTES`).
4. **The token is kept in browser localStorage** so a page refresh keeps you signed in. That is common for student projects. An httpOnly-cookie approach can be revisited during deployment (Module 10).
5. **No login rate limiting, password reset or email verification.** They are not required by the PDF. Rate limiting is noted for Module 10 security hardening.
6. **The `docker-compose.yml` file was validated but not started** in the development environment, because tests used a directly installed PostgreSQL 16. Start it on your machine with `docker compose up -d`.
7. **The CI workflow has not run yet.** It runs the first time the code is pushed to GitHub.
8. **Harmless test warning:** Starlette shows a deprecation notice about `httpx` in its test client. It does not affect results.

## Sprint review

All 12 backlog items are done, and every Module 1 requirement in the PDF is met. Two items depend on later modules (ticker existence, research tasks), and both are documented above instead of being faked. Next sprint (Module 2): stock search, OHLCV retrieval, data validation, and source/timestamp recording.
