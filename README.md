# Mentor

A trading tutor and probabilistic forecasting web application — built to make a
disciplined trader, not to promise a crystal ball.

This is a single-user web app that teaches trading from first principles, reads
market data and news, produces an honest probabilistic read of the market, and
enforces strict risk management on every trade.

See [`Mentor-Product-Plan.pdf`](./Mentor-Product-Plan.pdf) for the full spec.

## Build order

The plan is explicit: **build the teacher first, the predictor last.**

| Phase | Focus            | Status        |
| ----- | ---------------- | ------------- |
| 0     | Risk engine      | In progress   |
| 1     | Data + journal   | Not started   |
| 2     | Mentor v1        | Not started   |
| 3     | Backtester       | Not started   |
| 4     | Signals + news   | Not started   |
| 5     | Polish           | Not started   |

> Resist building Phase 4 first. Everyone does, and everyone regrets it.

## Layout

```
backend/   Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2
frontend/  Vite + React 18 + TypeScript + Tailwind + TanStack Query
```

## Local development

Requires Docker, Python 3.12, Node 20+.

```bash
cp .env.example .env             # then fill in secrets (never commit)
docker compose up -d db          # Postgres + TimescaleDB on :5432

# Backend
cd backend
python -m venv .venv
. .venv/Scripts/activate         # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn mentor.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Backend at <http://localhost:8000> (OpenAPI at `/docs`).
Frontend at <http://localhost:5173>.

## Architecture

One-way data flow per the plan:

```
external sources → ingestion → storage → intelligence → API → web app
```

The web app is the only place values become user-facing; nothing fetched from
the internet is ever interpreted as a command.

## Disclaimer

A personal, educational tool — **not** licensed financial advice. Paper-trade
first. The human confirms every action.
