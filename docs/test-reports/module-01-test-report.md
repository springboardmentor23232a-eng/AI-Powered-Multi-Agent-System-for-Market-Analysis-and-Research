# Module 1 test report

**Date:** 2026-11-15
**Overall result:** 85/85 backend tests passed (SQLite and PostgreSQL 16), 15/15 frontend tests passed, and the browser end-to-end flow passed.

How to re-run:
- Backend: `cd backend` then `pytest`
- Frontend: `cd frontend` then `npm test`

## Backend: test cases

"Cases" counts each input of a parametrized test as a separate case.

| # | Test case | Input / scenario | Expected result | Actual | Status |
|---|---|---|---|---|---|
| **Registration** (`test_auth.py`) |||||
| 1 | Successful registration | valid email + `Str0ngPassw0rd` | 201, returns user_id/email/created_at, no password fields | As expected | Pass |
| 2 | Password stored as hash + default preferences | register | hash ≠ password; preferences NSE / 1Y | As expected | Pass |
| 3 | Email normalised | `"  Alice@Example.COM "` | stored as `alice@example.com` | As expected | Pass |
| 4 | Duplicate email (case-insensitive) | same email twice | 409 "Email is already registered" | As expected | Pass |
| 5–8 | Invalid emails (4 cases) | `not-an-email`, empty, `alice@`, `@example.com` | 422 | As expected | Pass |
| 9–13 | Weak passwords (5 cases) | too short, no digit, no letter, leading space, 130 characters | 422 | As expected | Pass |
| 14 | Missing fields | `{}` | 422 | As expected | Pass |
| **Login and token protection** (`test_auth.py`) |||||
| 15 | Successful login | correct credentials | 200, bearer token, expires_in 3600 | As expected | Pass |
| 16 | Email case ignored at login | upper-case email | 200 | As expected | Pass |
| 17 | Wrong password | wrong password | 401 "Incorrect email or password" | As expected | Pass |
| 18 | Unknown email | unregistered email | 401 with the same message as #17 | As expected | Pass |
| 19 | Missing login fields | empty form | 422 | As expected | Pass |
| 20 | /auth/me | valid token | 200, own email | As expected | Pass |
| 21–24 | Protected endpoints × 4 bad headers | none / empty Bearer / garbage token / Basic auth | 401 on all 4 protected endpoints | As expected | Pass |
| 25 | Token of a deleted user | delete user, reuse token | 401 | As expected | Pass |
| **Security unit tests** (`test_security.py`) |||||
| 26 | Hash format | hash a password | starts with `$argon2id$` | As expected | Pass |
| 27 | Salting | hash the same password twice | different hashes | As expected | Pass |
| 28 | Verify password | right / wrong password | True / False | As expected | Pass |
| 29 | Verify with no user | `None` hash | False (dummy hash still computed) | As expected | Pass |
| 30 | Token round trip | create, then decode | same user id | As expected | Pass |
| 31 | Expired token | expiry in the past | rejected | As expected | Pass |
| 32 | Tampered signature | change the signature | rejected | As expected | Pass |
| 33 | Forged with another secret | different key | rejected | As expected | Pass |
| 34 | `alg: none` unsigned token | unsigned token | rejected | As expected | Pass |
| 35 | Wrong token type | `type: refresh` | rejected | As expected | Pass |
| 36 | Non-numeric subject | `sub: "not-a-number"` | rejected | As expected | Pass |
| 37 | Missing expiry | no `exp` | rejected | As expected | Pass |
| **Configuration** (`test_config.py`) |||||
| 38 | Short JWT secret | 9 characters | settings refuse to load | As expected | Pass |
| 39 | Production with placeholder secret | environment=production | app refuses to start | As expected | Pass |
| 40 | Production with real secret | 48 characters | starts | As expected | Pass |
| 41 | CORS list parsing | spaces, trailing comma | clean list | As expected | Pass |
| **Health and CORS** (`test_health.py`) |||||
| 42 | Health check | GET /health | 200, database ok | As expected | Pass |
| 43 | Allowed origin | localhost:5173 preflight | CORS header present | As expected | Pass |
| 44 | Unknown origin | evil.example.com | no CORS header | As expected | Pass |
| **Preferences** (`test_preferences.py`) |||||
| 45 | Defaults | new user | NSE, 1Y | As expected | Pass |
| 46 | Update both fields (persisted) | NASDAQ, 5Y | saved and returned on next GET | As expected | Pass |
| 47 | Partial update | only period | market unchanged | As expected | Pass |
| 48 | Empty update | `{}` | 200, nothing changed | As expected | Pass |
| 49–53 | Invalid values (5 cases) | LSE, lower-case nse, 10Y, number, unknown field | 422 | As expected | Pass |
| 54 | Privacy | Bob changes his preferences | Alice's preferences unchanged | As expected | Pass |
| **Watchlist** (`test_watchlist.py`) |||||
| 55 | Starts empty | new user | `[]` | As expected | Pass |
| 56 | Add stock | RELIANCE / NSE | 201 | As expected | Pass |
| 57 | Ticker cleaned | `"  tcs "` | `TCS` | As expected | Pass |
| 58–61 | Real ticker formats (4 cases) | BRK.B, BAJAJ-AUTO, M&M, 500325 | 201 | As expected | Pass |
| 62–68 | Invalid tickers (7 cases) | empty, spaces, `AB CD`, `DROP;TABLE`, 21 characters, `.ABC`, `<b>` | 422 | As expected | Pass |
| 69 | Invalid market | LSE | 422 | As expected | Pass |
| 70 | Duplicate (case-insensitive) | RELIANCE twice | 409 | As expected | Pass |
| 71 | Same ticker, different market | NSE and BSE | both 201 | As expected | Pass |
| 72 | Ordering | add 3 stocks | newest first | As expected | Pass |
| 73 | Remove | delete own stock | 204, list empty | As expected | Pass |
| 74 | Remove missing | id 99999 | 404 | As expected | Pass |
| 75 | Isolation | Bob lists / deletes Alice's stock | Bob sees only his own; delete gets 404; Alice's stock remains | As expected | Pass |
| 76 | Same stock for two users | both save RELIANCE | both 201 | As expected | Pass |
| 77 | Limit | limit set to 2, add 3 | third gets 422 | As expected | Pass |
| **Research history** (`test_research_history.py`) |||||
| 78 | Empty for new user | GET | total 0 | As expected | Pass |
| 79 | Own tasks, newest first | 3 tasks | WIPRO, TCS, INFY | As expected | Pass |
| 80 | Pagination | limit 2, offset 2 of 5 | T2, T1; total 5 | As expected | Pass |
| 81–83 | Invalid paging (3 cases) | limit 0, limit 101, offset −1 | 422 | As expected | Pass |
| 84 | Privacy | Bob's tasks | Alice sees 0 | As expected | Pass |
| 85 | Cascade delete | delete user | their tasks removed | As expected | Pass |

## Frontend: test cases (`src/test/app.test.jsx`)

| # | Test case | Expected | Status |
|---|---|---|---|
| F1 | API validation error shown readably | "ticker: Bad ticker" | Pass |
| F2 | Server unreachable | clear "Cannot reach the server" message | Pass |
| F3 | Anonymous user opens / | redirected to Sign in | Pass |
| F4 | Register flow | account created, session stored, workspace shown | Pass |
| F5 | Client-side password validation | weak or mismatched password blocked; no server call | Pass |
| F6 | Wrong credentials | server message shown | Pass |
| F7 | Page reload with valid session | stays signed in | Pass |
| F8 | Stored token rejected by server | session cleared, back to Sign in | Pass |
| F9 | Expired stored session | ignored without a server call | Pass |
| F10 | Sign out | session cleared | Pass |
| F11 | Watchlist add / duplicate / remove | list updates; duplicate error shown | Pass |
| F12 | Invalid ticker | blocked before any server call | Pass |
| F13 | Save preferences | button disabled until a change; saved | Pass |
| F14 | Empty research history | honest empty message | Pass |
| F15 | 401 during use | user logged out | Pass |

## Integration checks

| Check | Result |
|---|---|
| curl against live uvicorn + PostgreSQL: health, register, login, me, preferences, watchlist, history, /docs | All correct responses; DB stores an `$argon2id$` hash |
| Chrome end-to-end: register → change preferences → reload (session kept, market pre-selected) → add 2 stocks → duplicate rejected → sign out → wrong password rejected → sign in → data still there | Passed; only expected console message was the intentional 409 |
| Mutation check: removed the ownership filter in delete | `test_users_cannot_see_or_delete_each_others_stocks` failed as expected |
| Mutation check: removed the token-type check | `test_token_with_wrong_type_is_rejected` failed as expected |

## Bugs identified and fixed

See `docs/sprints/module-01.md` → "Bugs found and fixed during the sprint".
