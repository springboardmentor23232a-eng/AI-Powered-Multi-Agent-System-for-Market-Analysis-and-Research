# NetShield AI

AI-Powered Network Anomaly Detection and Predictive Intrusion Monitoring Platform.

**Module 1 — User Management**: JWT authentication (access token in memory + HttpOnly refresh cookie), role-based access control (Administrator / Security Analyst / Team Lead), team management, and audit logging — React + FastAPI + PostgreSQL 18.

## Architecture

```
React SPA (:5173) ──/api proxy──▶ FastAPI (:8000) ──▶ PostgreSQL 18 (:5432)
   access token in memory          JWT verify + RBAC deps      netshield DB
   refresh token: HttpOnly cookie  bcrypt password hashing     pgAdmin 4 GUI
```

- **Backend**: `backend/` — FastAPI, layered `routers → services → repositories`, raw SQL via `psycopg2` connection pool.
- **Frontend**: `frontend/` — React 18 + Vite + TailwindCSS (SOC dark theme) + Recharts.
- **Database**: `backend/migrations/001_init.sql` — schema, indexes, seed roles/permissions.

## Roles & Permissions

| Role | Access |
|---|---|
| `administrator` | Everything: users, roles/permissions, teams, audit logs, dashboards |
| `security_analyst` | Own dashboard, profile, view own teams (read-only) |
| `team_lead` | Dashboard, profile, manage teams they lead, team-scoped audit logs |

Permission enforcement is **backend-side** on every endpoint; the UI only hides/shows controls.

## Setup (Windows PowerShell)

### 1. Database

Create the database in pgAdmin 4 or psql:

```powershell
# Option A: pgAdmin Query Tool
CREATE DATABASE netshield;
```

```powershell
# Option B: psql (adjust user/port as needed)
psql -U postgres -c "CREATE DATABASE netshield;"
```

Apply the migration (pgAdmin Query Tool on the `netshield` DB, or):

```powershell
psql -U postgres -d netshield -f "C:\Users\saila\OneDrive\Desktop\NetShield AI\backend\migrations\001_init.sql"
```

### 2. Backend

```powershell
cd "C:\Users\saila\OneDrive\Desktop\NetShield AI\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
notepad .env   # set DATABASE_PASSWORD, JWT_SECRET, ADMIN_* values
```

Create the initial admin (credentials come from `.env` — never hardcoded):

```powershell
python scripts\create_admin.py
```

Run the API (works from the project root or `backend/` — `.env` is resolved relative to `backend/app/config.py`):

```powershell
# From project root:
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir backend --port 8000

# Or from backend/:
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Frontend

```powershell
cd "C:\Users\saila\OneDrive\Desktop\NetShield AI\frontend"
npm install
copy .env.example .env
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` to `localhost:8000`.

## API Endpoints (prefix `/api/v1`)

| Method | Endpoint | Auth / Permission |
|---|---|---|
| POST | `/auth/login` | public, rate-limited (5/5min), audited |
| POST | `/auth/refresh` | refresh cookie; rotates tokens |
| POST | `/auth/logout` | Bearer; revokes refresh token |
| GET | `/auth/me` | Bearer |
| POST | `/auth/me/password` | Bearer; revokes all sessions |
| GET/POST | `/users` | `users.view` / `users.create` |
| GET/PUT | `/users/{id}` | `users.view` / `users.update` |
| POST | `/users/{id}/status` | `users.activate` |
| PUT | `/users/{id}/roles` | `users.assign_roles` |
| GET | `/roles`, `/roles/permissions` | `roles.view` |
| GET/PUT | `/roles/{id}/permissions` | `roles.view` / `roles.manage` |
| GET/POST | `/teams` | `teams.view` / `teams.create` |
| GET/PUT/DELETE | `/teams/{id}` | view / `teams.update` / `teams.delete` |
| POST/DELETE | `/teams/{id}/members[/{user_id}]` | `teams.manage_members` |
| GET | `/audit-logs` | `audit.view` (team leads see team-scoped logs) |
| GET | `/dashboard/stats` | any authenticated user (role-scoped) |
| GET | `/network/packets/export.csv` | `reports.generate`; streams filtered packet metadata |

## Security notes

- Passwords hashed with **bcrypt**; never stored or logged in plaintext.
- Access tokens: JWT HS256, 30 min expiry, held **in memory only**.
- Refresh tokens: random 256-bit, **SHA-256 hashed at rest**, HttpOnly cookie, rotation + revocation on logout/password change.
- Login throttling: 5 attempts / 5 min per IP+identifier.
- Failed logins (including unknown usernames) are audit-logged with actor=NULL.
- Audit logs are **insert-only** — no update/delete endpoints exist.
- Set `COOKIE_SECURE=true` and strong `JWT_SECRET`/`DATABASE_PASSWORD` in production; serve over HTTPS.

## Project structure

```
NetShield AI/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app, router registration
│   │   ├── config.py             # env-based settings
│   │   ├── database.py           # psycopg2 connection pool
│   │   ├── security.py           # bcrypt + JWT helpers
│   │   ├── dependencies.py       # get_current_user, require_permissions
│   │   ├── rate_limit.py         # login throttle
│   │   ├── models/schemas.py     # Pydantic request models
│   │   ├── repositories/         # SQL per domain (user, role, team, audit, token)
│   │   ├── services/             # business logic + audit calls
│   │   └── routers/              # auth, users, roles, teams, audit, dashboard
│   ├── migrations/001_init.sql
│   ├── scripts/create_admin.py
│   ├── requirements.txt, .env.example
├── frontend/
│   └── src/{api,context,components,pages}
└── README.md
```

## Windows live packet capture

Live capture uses Scapy 2.6.1 with Npcap 1.89 on Windows. Install Scapy from the
backend requirements and keep Npcap installed and running. Npcap's service must
remain available, and Windows may require elevated privileges depending on the
selected adapter and Npcap installation options.

The capture foundation stores metadata only: timestamp, IP addresses, ports,
protocol, packet size, traffic direction, capture session, frame number, and
capture source. It does not store packet payloads or application content.

The Traffic Monitor can export historical, live, or combined packet metadata
as CSV. The authenticated `/api/v1/network/packets/export.csv` endpoint accepts
the packet filters used by the monitor and streams every matching row in
bounded database batches, independently of the visible packet page. CSV rows
include their capture source and available packet metadata; no payload or
application content is exported.

PCAPNG export is not supported. Historical imports contain metadata only, and
live capture discards raw packet bytes after extracting metadata. Without the
original frame bytes, a genuine PCAPNG cannot be reconstructed; synthesizing
packet contents would be misleading.

Apply migration `migrations/004_live_capture.sql` after migrations `001_init.sql`,
`002_packet_analysis.sql`, and `003_module2_permissions.sql`.

## Module 2+ readiness

New modules (Network Monitoring, Anomaly Detection, Intrusion Prediction, Alert Management, Analytics) plug in as additional `routers/` + `services/` + `repositories/`, new permission seeds in a new migration, and new frontend pages — the auth/RBAC/audit infrastructure is shared.
