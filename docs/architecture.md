# Architecture

## Big picture (target system, all 10 modules)

```
 React dashboard (frontend/)                       External data (Module 2+)
        │  HTTPS + JSON, JWT in Authorization header      market data, financials, news
        ▼                                                         ▲
 FastAPI backend (backend/app) ───────────────────────────────────┘
   ├── api/routes      HTTP endpoints (thin: validate input, call a service, return a schema)
   ├── services        business logic (no HTTP details)
   ├── agents/         Module 3–8: fundamental, technical, news, risk, supervisor, report
   ├── models          SQLAlchemy tables
   └── schemas         Pydantic request/response shapes
        │
        ▼
 PostgreSQL (SQLite allowed for local development and tests)
```

## What exists after Module 1

| Layer | Implemented now |
|---|---|
| Frontend | Register, login, protected workspace: watchlist, preferences, research history |
| API | `/auth/*`, `/users/me/preferences`, `/watchlist`, `/research/history`, `/health` |
| Services | `user_service`, `watchlist_service`, `research_service` |
| Database | All 7 tables created by the Alembic migration `0001_initial_schema` |

## Request flow example: adding a stock to the watchlist

1. The React `WatchlistCard` calls `api.addToWatchlist(token, "RELIANCE", "NSE")`.
2. `POST /api/v1/watchlist` arrives with `Authorization: Bearer <JWT>`.
3. `get_current_user` (api/deps.py) checks the token signature and expiry and loads the user. If anything is wrong, the reply is 401.
4. Pydantic `SavedStockCreate` trims and upper-cases the ticker and checks its format and the market. A bad value gets a 422 reply.
5. `watchlist_service.add_saved_stock` checks for duplicates and the per-user limit, then saves the stock.
6. The response is shaped by `SavedStockOut`, so only public fields are returned.

## Key design decisions

| Decision | Reason |
|---|---|
| One codebase, extended each week (no `module-N` copies) | The modules are parts of one application, and copies would drift apart |
| Routes → services → models | Agents in later modules can reuse services without going through HTTP |
| All tables created in Module 1 | The PDF requires the schema to be finalized in Milestone 1 |
| Enums stored as VARCHAR + CHECK constraint | Works the same on PostgreSQL and SQLite |
| Argon2id password hashing (pwdlib) | Current recommended algorithm for password storage |
| Stateless JWT access tokens (60 min) | Simple and standard. There is no refresh token, so users sign in again after expiry |
| OAuth2 password form for login | Makes the "Authorize" button in `/docs` work |
| Same error for unknown email and wrong password | Does not reveal which emails are registered |
| 404 (not 403) for other users' items | Does not reveal that the item exists |
| Settings only from environment variables | No secrets in Git (PDF requirement) |

## How later modules plug in

- **Module 2** adds `services/market_data/` and `/stocks/*` routes. The watchlist will then also check that a ticker exists.
- **Modules 3–6** add `agents/` with typed Pydantic outputs, stored in `agent_results.output_json`.
- **Module 7** creates `research_tasks` rows. The history endpoint and UI already display them.
- **Module 8** fills `research_reports` and `source_documents`.
- **Modules 9–10** extend the existing React app and the CI pipeline and add deployment.
