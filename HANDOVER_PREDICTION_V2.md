# Trade Mentor — Prediction & Features V2 Handover

**Created:** 2026-07-04
**Purpose:** Implement four improvements to prediction quality and product depth, the best way possible. This is a build spec for a fresh session — each feature is self-contained with architecture, data sources, files, algorithm, honest framing, and verification.

---

## 0. Guiding principle (do not violate)

This product's entire value is **honesty about uncertainty**. We have empirically proven this session:
- EUR/USD **direction** ≈ 53.5% out-of-sample over 10 years (a coin flip).
- **News sentiment** = 0% model importance.
- **More data** made the estimate honest, it did not create edge.

Therefore: **do not chase directional accuracy.** Every model must be measured out-of-sample and shipped only if it *measurably* beats a transparent baseline (the champion/challenger promotion gate already enforces this for the ML forecaster). If a feature doesn't help, say so and keep the simpler model. Never emit "buy" advice; emit context, probabilities, and track records.

---

## 1. Current state (what exists as of this handover)

**Stack:** Python 3.13 + FastAPI + SQLAlchemy 2.0 async + Pydantic v2 backend (strict layers: `api → application → domain`, domain pure, Decimal for money). Frontend: Vite + React 18 + TS strict + Tailwind + TanStack Query + Zod. PostgreSQL 17 (no Docker/Timescale). Live Anthropic mentor wired (`claude-opus-4-8`).

**Quality gates (all GREEN, keep them green):**
- Backend: `.\.venv\Scripts\ruff.exe check .`, `.\.venv\Scripts\mypy.exe src` (--strict, 154 files), `.\.venv\Scripts\python.exe -m pytest -q` (167 tests).
- Frontend: `npm run typecheck`, `npm run lint`, `npm run build`.

**Relevant existing machinery to REUSE (don't rebuild):**
- Forecasting: `domain/forecasting/{features,baseline,forecaster,regime,labels}.py`, `infrastructure/forecasting/sklearn_forecaster.py` (HistGradientBoostingClassifier, carries its own `_feature_names`/`_news_feature_names`, `forecast(..., news=)`), `model_store.py`.
- **News-feature wiring is the template for adding ANY exogenous feature** (macro/rates): `domain/forecasting/news_features.py` (point-in-time series → feature dict), `application/forecasting/news_context.py` (load series + `build_news_by_ts`), threaded through `training_service.py` (`include_news`), `inference_service.py`, `replay.py`. Copy this pattern for macro features.
- Prediction→outcome→calibration loop: `predictions` table, `resolver.py`, `application/forecasting/postmortem.py`, `promotion.py` (champion/challenger, Brier-gated), `scheduler/service.py` (APScheduler loop, opt-in `MENTOR_LOOP_ENABLED`).
- Market data: `adapters/{twelve_data,yahoo,failover,factory}.py`, `application/market/{ingestion_service,cross_source,quality}.py`. **Yahoo adapter fetches stocks too** (raw ticker) and FX (=X). Deep daily history: 2678 EURUSD daily bars 2016–2026.
- News tone (GDELT): `adapters/news/gdelt.py`, `repositories/news_tone.py`, `daily_news_tone` table — the template for a **`macro_series` table**.
- Stock tips: `domain/tips/*`, `application/tips/*`, `infrastructure/llm/tip_parser.py`, `adapters/stock_quotes.py`, `stock_tips` table, `api/v1/tips.py`, `pages/TipsPage.tsx`. Scorecard by category/action already works.
- Risk engine, journal, backtester, risk-of-ruin sim, alerts engine, economic calendar — all built.

**Run (one backend instance only):**
```
cd "D:\Trade mentor\backend"; .\.venv\Scripts\python.exe -m uvicorn mentor.main:app   # :8000
cd "D:\Trade mentor\frontend"; npm run dev                                             # :5173 (proxies /api)
.\.venv\Scripts\alembic.exe upgrade head                                              # migrations
```
DB: `mentor`/`mentor`, superuser pass `root`, service `postgresql-x64-17`. Keys in gitignored `D:\Trade mentor\.env` (ANTHROPIC_API_KEY, TWELVE_DATA_API_KEY set; NEWSAPI/FINNHUB empty). Model IDs: Opus 4.8 `claude-opus-4-8` ($5/$25), Sonnet 4.6 `claude-sonnet-4-6` ($3/$15), Haiku 4.5 `claude-haiku-4-5` ($1/$5).

---

## 2. Build order & dependencies

1. **Feature 1 — Volatility forecasting** (biggest honest win; self-contained; upgrades risk tools).
2. **Feature 2 — Macro/FX-driver features** (reuses news-feature wiring; benefits both direction & vol models).
3. **Feature 3 — Probability calibration** (wraps whatever models exist; do after #1/#2 so it calibrates the best model).
4. **Feature 4 — Tipster product features** (fully independent of the FX side; can be built any time / in parallel).

Each feature below is independently shippable with its own gates-green checkpoint. **De-risk every new external data source with a throwaway `httpx` probe FIRST** (as we did for GDELT/Yahoo/Stooq) before building an adapter — some endpoints have anti-bot walls or rate limits.

---

## 3. Feature 1 — Volatility forecasting (predict the *range*, not the *arrow*)

**Why it's honest:** Direction is ~random, but **volatility clusters** (big days follow big days) — one of the most robust empirical facts in finance (ARCH/GARCH). A vol model genuinely beats naive, unlike a direction model. Expect a *real* out-of-sample improvement here.

**Target:** future realized volatility over the next `H` bars: `future_rv[t] = stdev(logreturns[t+1 .. t+H])` (point-in-time label, same lookahead discipline as `labels.py`). Optionally also expose expected absolute range in pips.

**Design:**
- **Domain** `domain/forecasting/volatility.py`:
  - `realized_vol(returns, window)` and log-return helpers (Decimal-clean, mirror `features.py` style).
  - **EWMA baseline** (RiskMetrics λ=0.94): `ewma_vol` — transparent, strong, the yardstick the ML model must beat (analogous to `BaselineForecaster`). This is the "simple benchmark" per the plan.
  - `VolForecast` value object: `expected_vol`, `expected_range_pips`, `percentile_vs_history` (is today a wide/normal/calm day?), `reasoning`.
- **Features** (extend or a parallel builder): lagged realized vol at 5/10/20, ATR%, |ret_1|, high-low range %, vol-of-vol, day-of-week (FX session effects are real). Reuse `build_feature_series` shape.
- **Infra** `infrastructure/forecasting/sklearn_vol_forecaster.py`: `HistGradientBoostingRegressor` predicting `future_rv`. Same model-store save/load. `train_sklearn_vol_forecaster(bars, horizon)`.
- **Evaluation (honest):** out-of-sample **MAE**, **QLIKE** (proper vol loss), and **R² vs the EWMA baseline**. Report ML-vs-EWMA explicitly. A `_vol_eval.py` script like the news/source eval scripts.
- **API** `/forecasting/volatility` → `VolForecast` (expected move ±pips, wide/normal/calm, percentile). Add a `predict_vol` path to `inference_service.py` or a small `VolService`.
- **Integrations (the payoff):**
  - Position sizing: feed `expected_range` into stop-distance suggestions / the risk calculator.
  - Event-freeze: freeze/flag when predicted vol is in a high percentile.
  - Risk-of-ruin sim: drive the simulator's per-trade vol from the forecast instead of a static assumption.
- **Frontend:** on Forecast/Dashboard show "Expected move next 24h: ±X pips (calm/normal/wide, NNth pct)". Small card, reuse `Metric`.
- **Tests:** `realized_vol` correctness, EWMA recursion, VolForecast building, regressor train smoke test.

**Effort:** medium. **Ship criterion:** ML vol model beats EWMA on out-of-sample QLIKE/MAE (it should); if it doesn't, keep EWMA and say so.

---

## 4. Feature 2 — Real FX-driver features (rates + DXY + risk proxy)

**Why it's honest:** EUR/USD is driven by the **US–German interest-rate differential** and the **dollar index** far more than headlines — that's *why* news tone was 0%. This is the most fundamentally-defensible feature upgrade. Still largely priced in, so measure honestly; the promotion gate decides.

**Data sources (verify reachability with a probe first):**
- **FRED CSV, no key:** `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2` returns daily series. Useful ids: `DGS2` (US 2Y), `DGS10` (US 10Y), `T10Y2Y` (US 2s10s), `VIXCLS` (VIX), `DTWEXBGS` (broad USD index). (FRED API with a free key is the alternative if CSV is unreliable.)
- **Yahoo (existing adapter):** `DX-Y.NYB` (DXY), `GC=F` (gold), `^VIX`.
- German 2Y differential is the ideal but needs ECB/Bundesbank data (ECB SDW API, free) — do it as a v2.1 refinement; the US-side rates + DXY + risk proxy already capture most of the signal.

**Design (copy the GDELT news-tone + news-feature pattern exactly):**
- **Adapter** `adapters/macro/fred.py`: throttled `httpx`, parse CSV → `{day: value}` per series. Defensive like the GDELT adapter.
- **Table** `macro_series` (migration): `(series_id, day)` PK, `value` Numeric, `source`. Repo `MacroSeriesRepository` (upsert range, series). Mirror `news_tone.py`.
- **Ingestion** `application/macro/ingest.py` + endpoint `POST /macro/ingest` + CLI, backfill the series over the bar date range (2016–2026).
- **Features** `domain/forecasting/macro_features.py`: point-in-time (day ≤ asof). `MACRO_FEATURE_NAMES = (dxy_ret_5, us2y_chg_5, us_2s10s, risk_proxy_chg_5, ...)`. Pure builder from aligned series, exactly like `news_features.py`.
- **Wire into model** the SAME way news was: extend `train_sklearn_forecaster(..., macro_by_ts=)`, add macro names to `_feature_names`, thread through `training_service` (`include_macro`), `inference_service`, `replay`. The forecaster already generalizes over `_feature_names`, so this is additive.
- **Evaluation:** train with/without macro, compare Brier/accuracy out-of-sample (a `_macro_eval.py` script). Honest verdict either way.
- **Frontend (optional):** surface current macro context on the Data or Forecast page (DXY, US2Y, 2s10s, VIX with 1-line "what it means").

**Effort:** medium (one adapter + one table + feature module + wiring already patterned). **Ship criterion:** report the honest with/without delta; keep whichever model wins the gate.

---

## 5. Feature 3 — Probability calibration (make "60%" mean 60%)

**Why it's honest:** Raw classifier probabilities are usually mis-calibrated. Calibration won't raise accuracy — it makes the numbers *trustworthy*, which is the whole thesis.

**Design:**
- **Calibrator:** after training, fit **isotonic regression** (`sklearn.isotonic.IsotonicRegression`) — or Platt/sigmoid for small samples — on the held-out validation slice mapping raw `p_up → calibrated p_up`. Store it inside `SklearnForecaster` (new optional field, getattr-guarded like `_feature_names` for old-pickle compatibility). Apply in `forecast()` after `predict_proba`.
- **Conformal intervals:** split-conformal on the validation set to produce honest coverage bands. This is *especially* natural for the **vol regression target** (Feature 1) — conformal gives "expected move X ±Y with 90% coverage". For direction, report calibrated p ± band.
- **Metrics:** add **ECE (expected calibration error)** and reliability-curve data to `TrainingReport`. We already log calibration buckets in the audit loop — extend the calibration dashboard with a **reliability diagram** (predicted vs realized per bucket, with the diagonal).
- **Eval:** Brier and ECE before vs after calibration on out-of-sample.
- **Frontend:** reliability diagram on the calibration dashboard; show "calibrated 55% (±7%)" on the forecast.

**Effort:** low–medium. **Ship criterion:** post-calibration ECE < pre-calibration ECE on held-out; Brier no worse.

---

## 6. Feature 4 — Tipster product features (leaderboard + "follow him" backtest)

**Why it's honest:** No prediction claims — it's measurement and simulation of already-known outcomes. Real product value.

**Design (reuse tips + risk + backtest machinery):**
- **Multi-tipster leaderboard:** `GET /tips/leaderboard` — score every tipster (reuse `TipScoringService`), rank by mean return / win rate / a risk-adjusted measure (e.g. return ÷ stdev, or hit-rate × avg-win). Frontend leaderboard table; tipster selector already supported by schema.
- **"What if I'd followed him" backtest:** `POST /tips/backtest {tipster, risk_pct, exit_rule}` — for each tip: entry = mention price, size via the **existing risk engine** (risk_pct of a notional account, stop = e.g. mention − k·ATR), exit at now or by rule (time/stop/target). Build an equity curve; report total return, max drawdown, expectancy (R), % winners. Reuse `application/backtest/*` and `risk_simulator` pieces. Frontend equity curve (lightweight-charts) + stats.
- **Per-ticker technical context:** run the existing indicators/vol forecaster on each tracked ticker (trend, distance-from-high, expected move from Feature 1) so the tips table shows "dipping like he said?" objectively.
- **Alerts:** when a tracked ticker reaches the tipster's implied entry (e.g. his "buy on dip" reference), fire via the **existing alerts engine**.
- **Frontend:** extend `TipsPage.tsx` — tipster dropdown, leaderboard panel, "Backtest following [tipster]" button + equity curve. Keep the "not advice" disclaimers.

**Effort:** medium. **Ship criterion:** leaderboard + one honest "follow him" equity curve through the real risk engine, with drawdown and expectancy shown.

---

## 7. Cross-cutting checklist (every feature)

- [ ] Probe any new external data source with a throwaway `httpx` script before writing an adapter.
- [ ] New tables via Alembic migration (next rev after `20260702_0007`); keep ORM in `models.py`.
- [ ] Keep the layer boundary: domain pure, IO in application/infrastructure, DTOs in `api/v1`.
- [ ] Measure every model out-of-sample vs a transparent baseline; ship only if it wins; report honestly if it doesn't.
- [ ] Gates green before moving on: `ruff check .`, `mypy src` (strict), `pytest -q`, frontend `typecheck`/`lint`/`build`.
- [ ] Add tests for new pure domain logic (vol math, macro features, calibration mapping, tip backtest).
- [ ] No financial advice; disclaimers in payloads + UI.

## 8. Known gotchas (bit us this session)

- **Only ONE backend instance** on :8000 — kill stragglers with `Get-NetTCPConnection -LocalPort 8000 -State Listen` → `Stop-Process -Force`. uvicorn is started WITHOUT `--reload`, so restart it to pick up code.
- **Yahoo daily timestamps** are at exchange-local midnight (23:00 UTC prior day, BST) — `yahoo._normalise_ts` snaps D1 to nearest UTC midnight so they dedupe with Twelve Data. Any new daily source needs the same alignment.
- **GDELT / free APIs rate-limit** (1 req/5s) — throttle + retry with backoff; make secondary calls best-effort.
- **mypy --strict** rejects bare `dict`/`list`/`Sequence` (need type args), `Returning Any`, and stale `type: ignore`. Use typed Pydantic response models, not `response_model=dict`.
- **PowerShell 5.1**: no ternary/`&&`; use `if/else`. Non-ASCII in test prints can hit cp1252 — keep script output ASCII.
- **pydantic-settings**: external keys reach code via `validation_alias` in `config.py`; add new keys there.
- **Old model pickles**: when changing `SklearnForecaster` fields, keep them `getattr`-guarded with defaults so old joblibs still load (or just retrain).
- **Browser preview** was blocked by an unrelated chat's server on :5173; verify via HTTP + zod-schema match if preview is unavailable.

## 9. First actions for the new session

1. Read this file + memory (`project_trade_mentor.md`).
2. Confirm gates are green and backend runs.
3. Start **Feature 1 (volatility)**: probe nothing (uses existing bars), build `domain/forecasting/volatility.py` + EWMA baseline first, then the regressor, then the honest ML-vs-EWMA eval, then API + a small frontend card, then integrate into position sizing / event-freeze.
4. Proceed through Features 2 → 3 → 4, each to a gates-green checkpoint.
