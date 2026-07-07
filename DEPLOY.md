# Deploying Mentor (single-user)

Mentor ships as **one service**: the image builds the React frontend and the
FastAPI backend serves it from the same origin (so there's no CORS to fight),
applies database migrations on start, and **refuses to boot in production if
the auth/JWT/DB secrets aren't set** — so you can't accidentally publish an open
API.

This guide is for a personal, single-user deploy (only you log in).

---

## 1. Generate your secrets (once)

You need three secrets before deploying:

**Password hash** — the single login. From `backend/` with the venv:
```
.\.venv\Scripts\python.exe -m mentor.cli.hash_password
```
It prompts for a password and prints a bcrypt hash → that's `MENTOR_AUTH_PASSWORD_HASH`.

**JWT secret** — signs your session token (≥ 32 chars):
```
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
→ `MENTOR_JWT_SECRET`.

**Database password** — any strong random string → `MENTOR_DB_PASSWORD`.

Keep the Anthropic and Twelve Data keys handy too (from your current `.env`).
**If the Anthropic key has ever been shared anywhere, rotate it first.**

---

## 2a. Deploy on a VPS or your own box (Docker Compose)

The simplest self-hosted path — Postgres + app in one command.

1. Copy `.env.example` to `.env` at the repo root and fill in:
   ```
   MENTOR_ENV=production
   MENTOR_DB_PASSWORD=...            # strong random
   MENTOR_AUTH_USERNAME=you
   MENTOR_AUTH_PASSWORD_HASH=...     # from step 1
   MENTOR_JWT_SECRET=...             # from step 1
   ANTHROPIC_API_KEY=...
   TWELVE_DATA_API_KEY=...
   # MENTOR_CORS_ORIGINS is not needed (frontend is same-origin)
   ```
2. Build and start:
   ```
   docker compose -f docker-compose.prod.yml up -d --build
   ```
3. Put it behind HTTPS. Easiest is **Caddy** as a reverse proxy (auto TLS):
   ```
   your-domain.com {
     reverse_proxy localhost:8000
   }
   ```
   Never expose port 8000 directly to the internet — only through the TLS proxy.

The app is at your domain; log in with your username + password.

## 2b. Deploy on a platform (Render / Railway / Fly.io)

These give you HTTPS and a managed Postgres automatically.

1. Push this repo to GitHub (private), create a **Web Service** from it — it uses
   the root `Dockerfile` (no build command needed; the port is injected as `$PORT`).
2. Add a **managed Postgres** and point the app at it via `MENTOR_DB_HOST`,
   `MENTOR_DB_PORT`, `MENTOR_DB_NAME`, `MENTOR_DB_USER`, `MENTOR_DB_PASSWORD`.
3. Set the env vars (as service secrets, not in the repo):
   `MENTOR_ENV=production`, `MENTOR_AUTH_USERNAME`, `MENTOR_AUTH_PASSWORD_HASH`,
   `MENTOR_JWT_SECRET`, `ANTHROPIC_API_KEY`, `TWELVE_DATA_API_KEY`.
4. Deploy. Migrations run on start; the app serves the frontend at `/`.

---

## 3. Required environment variables

| Variable | Required | Notes |
|---|---|---|
| `MENTOR_ENV` | yes | Set to `production`. Enables the security guard + hides API docs. |
| `MENTOR_AUTH_PASSWORD_HASH` | yes | bcrypt hash from step 1. Without it, startup refuses. |
| `MENTOR_JWT_SECRET` | yes | ≥ 32 chars. |
| `MENTOR_DB_PASSWORD` | yes | Strong; not `change-me`. |
| `MENTOR_DB_HOST/PORT/NAME/USER` | yes* | Point at your Postgres (compose sets `HOST=db`). |
| `MENTOR_AUTH_USERNAME` | no | Defaults to `mentor`. |
| `ANTHROPIC_API_KEY` | no | Needed for the LLM mentor + tip parsing. |
| `TWELVE_DATA_API_KEY` | no | Intraday price data (Yahoo is the free fallback). |
| `MENTOR_CORS_ORIGINS` | no | Only if you host the frontend on a *separate* origin. |
| `MENTOR_LOOP_ENABLED` | no | `true` to run the in-process ingest/predict loop (keeps data fresh). |

---

## 4. After first deploy

- **Log in** with your username + password.
- **Backfill price data** (the app ships with models but not fresh bars). One-off
  inside the container / on the host:
  ```
  python -m mentor.cli.ingest --symbol EURUSD --timeframe 1d --days 3650 --source yahoo
  python -m mentor.cli.ingest --symbol EURUSD --timeframe 1h --days 120
  ```
- **Keep it fresh**: set `MENTOR_LOOP_ENABLED=true`, or run the ingest command on a
  cron. Otherwise charts/forecasts go stale.

---

## 5. What the security guard enforces

On `MENTOR_ENV=production`, the app **will not start** unless:
- `MENTOR_AUTH_PASSWORD_HASH` is set (otherwise the whole API would be open),
- `MENTOR_JWT_SECRET` is set, not the placeholder, and ≥ 32 chars,
- `MENTOR_DB_PASSWORD` is set and not `change-me`.

It also hides the interactive API docs, rate-limits login, and every API endpoint
(including the ones that spend money — `/explain`, `/tips/ingest`, and the Yahoo
scrapes) requires a valid token. Health and login are the only open API routes.

Not licensed financial advice — a personal, educational tool. Paper-trade first.
