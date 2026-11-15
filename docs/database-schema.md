# Database schema

Created by `backend/alembic/versions/0001_initial_schema.py`. Verified on PostgreSQL 16 and SQLite: upgrade, downgrade and `alembic check` all succeed.
All timestamps are timezone-aware (UTC).

```
users ─┬─< user_preferences (1:1)
       ├─< saved_stocks
       └─< research_tasks ─┬─< agent_results
                           ├─< source_documents
                           └── research_reports (1:1)
```
Deleting a user deletes all their rows (ON DELETE CASCADE).

## Tables from the project specification

| Table | Columns | Notes |
|---|---|---|
| users | user_id PK, email (unique), password_hash, created_at | Email stored lower-case; Argon2id hash only |
| research_tasks | task_id PK, user_id FK, ticker, market, requested_period, status, created_at, completed_at | status: pending, running, completed, partial, failed. Filled from Module 7 |
| agent_results | result_id PK, task_id FK, agent_name, status, output_json, error_message, created_at | status: success, failed, unavailable. JSONB on PostgreSQL |
| source_documents | source_id PK, task_id FK, source_type, title, source_url, published_at, retrieved_at, content_hash | content_hash = SHA-256 of the fetched content |
| research_reports | report_id PK, task_id FK (unique), report_content, summary, limitations, created_at | One report per task |
| saved_stocks | saved_stock_id PK, user_id FK, ticker, **market**, created_at | Unique (user_id, ticker, market) |

## Additions to the specification (and why)

| Addition | Why |
|---|---|
| `user_preferences` table (user_id PK/FK, default_market, analysis_period, updated_at) | Module 1 requires preferences, but `users` has no columns for them |
| `saved_stocks.market` | The same symbol can be listed on NSE and BSE, so the ticker alone is ambiguous |

## Allowed values

- market: `NSE`, `BSE`, `NYSE`, `NASDAQ` (default `NSE`)
- analysis period: `1M`, `3M`, `6M`, `1Y`, `2Y`, `5Y` (default `1Y`)
