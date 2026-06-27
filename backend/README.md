# Mentor — Backend

Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic v2

## Layout

```
src/mentor/
├── api/                FastAPI transport — routers, deps, error translation
│   ├── deps.py         Settings + DB session dependencies
│   ├── errors.py       Domain → HTTP mapper
│   └── v1/             Versioned endpoints (health, risk, …)
├── application/        Use-case orchestration (intentionally empty in Phase 0)
├── domain/             Pure trading logic — zero framework deps
│   ├── money.py        Decimal value objects: Money, Percent
│   ├── instruments.py  Instrument mechanics (pip, contract, lot step)
│   ├── errors.py       DomainError / ValidationError
│   └── risk/           Position sizing, expectancy, guardrails, stops
├── infrastructure/     DB engine, ORM base, future models
├── config.py           Pydantic settings (env-driven, frozen)
├── logging.py          structlog setup
└── main.py             FastAPI app factory + ASGI entrypoint
```

The dependency direction is strictly inward: `api` → `application` → `domain`.
The domain never imports framework code, which is why every risk-engine
rule is covered by a fast in-memory test that needs no fixtures.

## Running locally

```bash
python -m venv .venv
. .venv/Scripts/activate                # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# In another shell, start the database
docker compose -f ../docker-compose.yml up -d db

# Apply migrations (no-op in Phase 0 — domain is stateless)
alembic upgrade head

uvicorn mentor.main:app --reload
```

OpenAPI explorer: <http://localhost:8000/docs>.

## Tests

```bash
pytest                          # full suite
pytest tests/domain -q          # domain-only (fastest)
pytest --cov=mentor             # with coverage
```

The position-sizing test uses Hypothesis to assert the **risk-budget
invariant**: across hundreds of randomly generated accounts and trade
parameters, the realised cash at risk never exceeds the user's stated
budget. This is the single most important property in the whole engine —
a bug there would silently bankrupt a trader.

## Lint & type-check

```bash
ruff check .
mypy src
```

Ruff is configured strictly (bugbear, bandit, pyupgrade, async-correctness).
Mypy is in `strict` mode. Both are CI gates.

## Adding a new instrument

Add it to `BUILTIN_INSTRUMENTS` in `mentor/domain/instruments.py`. Mechanics
that need configuring: `pip_size`, `contract_size`, `min_lot`, `lot_step`.
No other code change is required — the calculator, guardrails, and API
all derive their behaviour from the instrument.

## Phase-0 invariants (read these before changing risk code)

1. Money is always `Decimal`. Float math is forbidden in the domain.
2. Position size always rounds **down** to the lot step. The risk budget
   is a ceiling, never a target.
3. Domain raises `ValidationError` / `GuardrailBreach`. The API layer is
   the only place that maps these to HTTP codes.
4. Guardrail checks return a `GuardrailReport` rather than raising —
   the UI needs to show the user *why* a trade is blocked.
