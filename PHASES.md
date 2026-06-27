# Build phases

The plan is explicit:

> Build the teacher first. Let the predictions be humble. Let the risk engine
> be strict. That is how people who are still trading after fifteen years
> build things.

Phases follow the product plan exactly. Skipping ahead is the costliest
mistake on a project like this — Phase 4 looks shinier than Phase 0 but
unvalidated signals teach lessons by emptying the account.

## Phase 0 — Risk engine ✅ in progress

The foundation. A trader without forecasting can still survive; a trader
without sizing discipline cannot.

- [x] Money / Percent value objects with strict Decimal math
- [x] Instrument mechanics (pip, contract, lot step) — EUR/USD + 6 others
- [x] Position sizing (round-down, risk budget is a ceiling)
- [x] R:R and expectancy
- [x] ATR-based stop helper
- [x] Account guardrails (per-trade, open risk, daily loss)
- [x] HTTP API for all of the above
- [x] Property-based test: risk never exceeds the stated budget
- [x] Risk Calculator UI with contextual explainers on every metric

## Phase 1 — Data + journal ✅ in progress

- [x] TimescaleDB schema + initial migration (`price_bars` hypertable, `trades`, `journal_reflections`)
- [x] Market-data adapter pattern + Twelve Data implementation with tenacity retries
- [x] Ingestion service (idempotent, `INSERT … ON CONFLICT DO NOTHING`)
- [x] CLI for manual backfill (`python -m mentor.cli.ingest`)
- [x] Data-quality scanner (gaps, duplicates, stale-feed timestamp)
- [x] Trade aggregate with planned → open → closed state machine
- [x] Deterministic R-multiple recomputation at close (long & short symmetric)
- [x] Journal analytics (win rate, expectancy, total R, profit factor)
- [x] Pre-trade checklist (reason, stop, target, R:R, size, guardrails)
- [x] API endpoints: `/trades` CRUD + `/close`, `/journal/analytics`, `/checklist/pre-trade`, `/prices/{symbol}`
- [x] Frontend Journal page with gated new-trade form + live checklist + analytics panel
- [x] Multi-timeframe chart (lightweight-charts) on the Prices page, with gap markers

## Phase 2 — Mentor v1 ✅ in progress

- [x] Adaptive curriculum lesson tree with 7 modules / 22 lessons (the plan's exact module list)
- [x] Lesson progress persisted (`lesson_progress` table); content is code-shipped immutable
- [x] `explain(metric, context)` service — Anthropic adapter with stub fallback when no key
- [x] Prompt-injection mitigations (whitelisted topics, fenced context, system-prompt instructions)
- [x] `/curriculum/overview`, `/curriculum/lessons/{slug}`, `/explain` endpoints
- [x] Frontend Lessons page with module tree + lesson reader + progress marking
- [x] Inline `Why?` button on Risk Calculator that calls `/explain` with the live values
- [ ] Socratic mode (V2) — defer per plan priority

## Phase 3 — Backtester ✅ in progress

- [x] Event-driven engine: fills happen at the *next* bar's open, never the current close
- [x] `MarketView` with structural no-lookahead — no public method can reach a future bar
- [x] Full transaction-cost modelling (spread, slippage, commission); no "frictionless" mode
- [x] Pure-function indicators (SMA, EMA, ATR, RSI) shared with the (Phase 4) signals pipeline
- [x] Baseline `MaCrossover` + `BuyAndHold` strategies — the honest yardstick
- [x] Strategy registry so the frontend can drive new strategies by name+params
- [x] Metrics: return, drawdown, sharpe-ish, win rate, expectancy, profit factor, costs paid, forced closes
- [x] `WalkForwardResult` with in-sample vs. out-of-sample expectancy + degradation %, plus an overfit heuristic
- [x] `BacktestRunner` application service loading from TimescaleDB
- [x] `POST /backtest` + `GET /backtest/strategies` API
- [x] Frontend Backtester page with equity curve, metrics, walk-forward panel, last-trades table
- [x] Tests: lookahead-impossibility, fill-on-next-bar, cost-widens-fill, stop-within-range, walk-forward
- [ ] Monte-Carlo sequence test (V2 per plan — defer)
- [ ] Strategy comparison side-by-side (multi-run dashboard) — V2

## Phase 4 — Signals + news ✅ in progress

- [x] Feature engineering (lagged returns, EMA distances, RSI, MACD, ATR, range distance, vol) — pure point-in-time
- [x] Baseline rule forecaster — capped [0.30, 0.70] so it never pretends to be sure
- [x] ML forecaster (sklearn `HistGradientBoostingClassifier`) — outputs P(up), never a price target
- [x] Training service + model store (joblib + JSON metadata sidecar)
- [x] News ingestion via NewsAPI adapter with tenacity retries
- [x] LLM news classifier (Anthropic), categorises macro / regulatory / geopolitical / risk-off / hype / other; stub fallback
- [x] Prediction audit log table + `resolve_pending_predictions` closer for the calibration loop
- [x] Calibration summary endpoint (hit rate per 10% probability bucket)
- [x] Forecast API: `/forecasting/predict`, `/forecasting/snapshot`, `/forecasting/train`, `/forecasting/models`, `/forecasting/audit*`
- [x] News API: `/news`, `/news/ingest`
- [x] Frontend Forecast page: probability + reasoning + news context + audit log + resolver
- [ ] Confidence calibration **dashboard** (V2) — endpoint exists, dashboard UI deferred
- [ ] Economic calendar adapter — defer to Phase 5
- [ ] Regime detection / model explainability (V2)

## Phase 5 — Polish ✅ in progress

- [x] **Unified morning-briefing dashboard** — calm one-screen view of today's lean, news, journal pulse, open risk, event-freeze banner
- [x] **Risk-of-ruin Monte Carlo simulator** — sampled from the user's R-distribution; reports p_ruin, p5/p50/p95 terminal balance, p95 drawdown
- [x] **Alerts** — persisted price/signal/event-freeze alerts with sweep + create + disable + delete
- [x] **Event-freeze evaluator** — domain function + `/alerts/event-freeze` endpoint + banner on dashboard
- [x] **Calibration chart** — stated-vs-realised bars per probability bucket on the Forecast page
- [x] Dashboard becomes the default landing page
- [x] **Annotated chart** — trade markers (entry arrows, exit squares colour-coded by R) overlaid on the Prices chart
- [x] **Strategy comparison** — pin a backtest as baseline, run another, get overlaid equity curves + side-by-side metrics + winner badge
- [x] **Single-user auth** — bcrypt password hash CLI, JWT login, middleware gating `/api/v1`, frontend login page + token store
- [x] **Regime detection** — `FeatureDistribution` captured at training time; `RegimeAdjustedForecaster` scales confidence by regime fit and abstains below threshold
- [x] **Economic calendar** — `EconomicCalendarAdapter` ABC + Finnhub adapter; events stored in TimescaleDB-adjacent Postgres table; event-freeze now consults both classified news *and* scheduled releases
- [x] Economic calendar widget on Dashboard
- [ ] Socratic mode + spaced-repetition quizzes — V2
