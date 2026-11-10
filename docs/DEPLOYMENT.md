# Deployment

Single-host deployment: Caddy (automatic HTTPS) in front of the React app, the FastAPI API and PostgreSQL.
Only ports 80 and 443 are public; the database and API are on the internal Docker network.

## Prerequisites
- A Linux VM (2 GB RAM is enough) with Docker and the Compose plugin.
- A domain with an A record pointing at the VM, and ports 80 and 443 open.

## First deploy
```
cp .env.production.example .env.production     # set DOMAIN, POSTGRES_PASSWORD, JWT_SECRET (and LLM_API_KEY if used)
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```
Migrations run automatically when the backend starts. The API refuses to start in production with a short or default
`JWT_SECRET`, a SQLite database, or wildcard CORS.

## Smoke test (do this once after every first deploy)
1. `https://<DOMAIN>/api/health` returns `{"status":"ok"}`; `https://<DOMAIN>/api/ready` returns `{"status":"ready"}`.
2. Register, search "Infosys", start research, and watch it reach `completed` or `partial`.
3. Open the Charts tab (confirms the Content-Security-Policy in `deploy/Caddyfile` allows Plotly) and download the report.
4. `docker compose -f docker-compose.prod.yml logs backend` shows one JSON line per request, with no tokens or passwords.

## Operations
| Task | Command |
|---|---|
| Update | `git pull && docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build` |
| Logs | `docker compose -f docker-compose.prod.yml logs -f backend` |
| Backup | `docker compose -f docker-compose.prod.yml exec -T db pg_dump -U veritas veritas \| gzip > veritas_$(date +%F).sql.gz` |
| Restore | `gunzip -c veritas_<date>.sql.gz \| docker compose -f docker-compose.prod.yml exec -T db psql -U veritas veritas` |

Schedule the backup with cron and copy the file off the host.

## Access controls and limits
- Every research, watchlist and preference endpoint requires a JWT and is scoped to the signed-in user.
- Login and registration: 10 attempts per minute per client IP (`AUTH_ATTEMPTS_PER_MINUTE`).
- Per user: 3 concurrent research tasks and 30 per day (`MAX_ACTIVE_TASKS_PER_USER`, `MAX_TASKS_PER_DAY`) to cap data-provider and LLM cost.
- API docs are disabled in production. CORS allows only `https://<DOMAIN>`.

## Known constraints
- **Run one API worker.** The rate limiter and background tasks live in the API process. Scaling out needs a shared
  limiter (for example Redis) and a task queue; neither is built.
- A restart interrupts running tasks. On startup, tasks left queued or running for more than 30 minutes are marked
  `failed` so users can rerun them.
- Data comes from yfinance and a public news RSS feed. Both are unofficial and can change or rate-limit without
  notice; failures degrade the report (marked unavailable) rather than breaking it.
- Run `python -m app.evaluation.run` against the deployed configuration before relying on the numbers.
