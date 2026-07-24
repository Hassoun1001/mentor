# The Mentor algorithm, end to end

What the system does, in the order it does it, with the actual constants.

The organising idea is worth stating first, because every design choice
below follows from it: **the hard part is not predicting, it is refusing to
believe your own predictions.** Any model can produce a number. This system
is built to decide whether that number has earned trust, and to say no —
loudly, and by default — when it hasn't.

---

## 0. What it predicts, and what it refuses to

Two lanes run independently, each with its own champion:

| Lane | Timeframe | Horizon | Meaning |
|---|---|---|---|
| **H1** | 1 hour bars | 24 bars | direction over the next day |
| **D1** | 1 day bars | 5 bars | direction over the next trading week |

Symbol is `EURUSD` throughout (`loop_symbol`).

Both lanes predict **P(up)** — the probability the close at `horizon` is
above the close now. They do not predict price, magnitude, or timing.

Separately, a **volatility** model predicts *how far* price will move,
which turns out to be the only thing the system forecasts well.

---

## 1. Data layer

### Ingestion
`FailoverMarketDataAdapter` tries Twelve Data, falls back to Yahoo Finance.
Only Yahoo is configured in production (no Twelve Data key), which means
**every bar is single-sourced and unverified** — cross-source comparison
is unavailable.

Bars are upserted by `(symbol, timeframe, ts)`, so re-fetching is
idempotent and a partial bar is overwritten by its completed version.

### Point-in-time discipline
Every feature at bar `i` is built from `bars[:i+1]` only. The one place
this needs care is higher-timeframe context: a D1 bar stamped `ts` is not
*complete* until `ts + 86400`, so `HtfSeries._visible(ts)` filters on **bar
close times**, not bar timestamps. Without that, an H1 model would see the
whole of today's daily bar while predicting from inside it.

### Known data facts
- **Weekends are not gaps.** FX prints nothing from Friday evening to
  Sunday night. `_is_weekend_closure` walks the *missing* timestamps (not
  the endpoints — a daily bar is stamped at midnight) and excludes those
  holes. 57 of 59 daily "gaps" were weekends.
- **The newest bar is usually unfinished.** Yahoo labels the in-progress
  FX session by its close date, so the daily series routinely carries a bar
  dated *tomorrow*. The quality scanner counts `future_bars` (period not
  started) separately from `forming_bars` (mid-period). Both are reported;
  neither is dropped, because dropping the current bar costs the live price.

---

## 2. Features

Four families, assembled per bar in a fixed column order the model carries
with itself so technical-only and enriched models share one class.

**Technical** (`FEATURE_NAMES`) — returns over several lookbacks, EWMA and
realized volatility, distance to rolling high/low, trend filters.

**News tone** (`NEWS_FEATURE_NAMES`) — GDELT daily sentiment for a EUR/USD
query. Free, no key. Missing days default to neutral `0.0`.

**Macro** (`MACRO_FEATURE_NAMES`) — FRED series: DXY, VIX, rate spreads,
and their changes. *The FRED adapter must never send a custom User-Agent* —
their WAF blocks datacenter IPs that do, while default tool UAs pass.

**Higher timeframe** (`HTF_FEATURE_NAMES`) — `htf_trend_dist`,
`htf_ema_spread`, `htf_rsi`, `htf_atr_pct`, `htf_range_pos`, computed on D1
and projected onto H1 timestamps under the close-time rule above.

---

## 3. Direction models

### The baseline rule
`BaselineForecaster` — a fixed formula over a 200-bar trend filter. **No
fitted parameters.** That matters twice: it is the fallback when no
champion exists, and it is the only model that can honestly be replayed
over history, because it cannot have seen the outcomes.

### The trained model
`HistGradientBoostingClassifier`, `max_iter=200`, trained on at most
`loop_train_max_bars = 6000` bars.

The split is **train → calibration → test**, walking forward, with an
**embargo of `horizon_bars` between each**:

```
fit_end = calib_start - embargo
calib   = [calib_start, calib_end)          calib_size = max(30, 15% of train)
embargo
test    = last 20%
```

Without the embargo, the last training sample's outcome window overlaps
the first calibration sample — label leakage across the seam.

### Calibration
Isotonic regression fitted on the calibration slice. **Shipped only if it
reduces ECE without worsening Brier on test** — the same "beat the
baseline or stay simple" rule the champion gate applies to models.

### Feature importance
Permutation importance on the calibration slice, `n_repeats=5`, scored by
`neg_brier_score`. HGB exposes no gain-based `feature_importances_`, so the
original attribute lookup silently produced all zeros. Skipped during
walk-forward selection (`compute_importances=False`) since only the Brier
is read there.

### Selective prediction (abstention)
The model may learn a **margin** on `|p_up − 0.5|` and stay silent below it.

- Margin chosen on the **calibration** slice, graded on **test**. A
  threshold picked and scored on the same data describes that data; only
  one that survives fresh data is a rule.
- **Coverage floor `MIN_COVERAGE = 0.15`** — a policy must be willing to
  act on 15% of hours. Without it the search keeps the four luckiest hours
  and reports a spectacular Brier.
- **Minimum gain `_MIN_GAIN = 0.002`** — abstention must *buy* that much
  Brier or it is refused. Measured on live EUR/USD, an unconstrained search
  discarded 74% of hours for a ~0.0001 improvement that promptly reversed.

**Empirically: abstention has never been earned.** Every model comes back
at margin 0.0 — the confident hours score no better than the rest.

---

## 4. Volatility model

### EWMA baseline
Exponentially weighted realized volatility → 1-sigma expected move over the
horizon via `horizon_move_pips`: `σ_bar × √H × close ÷ pip_size`.

### ML volatility
`HistGradientBoostingRegressor` on volatility features plus macro, with a
split-conformal residual quantile producing a **90% band**.

**It cannot train at `horizon_bars < 2`** — the label is the sample
standard deviation of returns *inside* the window, and one bar holds one
return with no spread. It says so explicitly and names EWMA as the
alternative.

### Which one ships
`report.beats_ewma` decides, on MAE and QLIKE against the EWMA baseline.
At horizon 5 the ML model does win (MAE 0.00142 vs 0.00161, QLIKE 0.478 vs
0.510, n=514) — but the trade plan asks for horizon 1, where it cannot run,
so **the EWMA is what actually feeds every stop distance.**

### The audit
`VolReplayService` replays the forecaster over history — point-in-time,
**non-overlapping windows**, capped at 800 visible bars and 400 samples —
and grades two claims separately:

1. **The 1-sigma claim.** Under a normal walk, 68.27% of moves should land
   inside. Measured: **70.2%** at h=1 (95% CI [65.6%, 74.5%]), **69.0%** at
   h=5. The claim holds.
2. **The band claim.** Reported separately, because the conformal quantile
   is fitted on *volatility prediction errors* — it is an interval around
   the sigma estimate, not a prediction interval for the move.

A sigma is not an average move: `E|X| = 0.798σ`, `median|X| = 0.674σ`. The
audit scores accuracy against the sigma's **implied mean absolute move**
and measures bias against the median calibration predicts, so 1.0 means
calibrated. Scoring σ against `|realised|` directly manufactures a 25%
error and hands a free win to any benchmark predicting an average.

---

## 5. The promotion gate — the honesty core

Run weekly, or immediately when drift fires.

```
1. SELECT   train 7 candidate configs across walk-forward folds (0.64, 0.80)
            score each by mean effective Brier
            candidates: technical, +macro, +news+macro, regularized,
                        pruned, +htf, +macro+htf
2. TRAIN    retrain only the winning family on the full window
3. REGRADE  re-score the incumbent on the SAME fresh tail, under its OWN
            abstention margin (evaluate_policy_on_tail)
4. GATE     promote only if BOTH:
              challenger ≤ champion − 0.002        (_PROMOTION_MARGIN)
              challenger ≤ 0.248                   (_BASELINE_FLOOR)
              and, if abstaining, coverage ≥ 0.15
5. DEMOTE   if the incumbent's fresh re-grade exceeds 0.248 on
            3 consecutive retrains (_DEMOTION_AFTER) → fall back to baseline
6. LOG      append the decision to promotions.jsonl and the post-mortem
            to lessons.jsonl, which feeds the next retrain
```

`_BASELINE_FLOOR = 0.25 − 0.002 = 0.248`. A Brier of 0.25 is a coin flip.
**Beating a bad incumbent is not the same as being good**, so a challenger
that wins the head-to-head but misses the floor is not promoted.

`effective_brier` = covered Brier when the model abstains, all-hours Brier
otherwise. Models trained before abstention existed carry zeros, so the
fallback prevents a legacy model reading as a perfect 0.0.

---

## 6. The autonomous loop

APScheduler, in-process. **Every refresh job fires 45s after boot**
(`_STARTUP_DELAY_SECONDS`) — interval jobs otherwise first run one whole
interval *after registration*, so every deploy silently reset every clock.

| Job | Cadence | Notes |
|---|---|---|
| `ingest` / `ingest_d1` | 60 min / 24 h | failover adapter |
| `predict` / `predict_d1` | 60 min / 24 h | gated by data quality |
| `resolve` | 15 min | grades matured predictions |
| `news_tone` | 6 h | skips if already current — GDELT rate-limits hard |
| `retrain` / `retrain_d1` | weekly | **anchored to promotions.jsonl**, not boot |

Retraining is deliberately excluded from the startup kick — it costs about
an hour of CPU — but is scheduled from *the last recorded retrain* plus the
interval, so frequent deploys can't push it out forever. An overdue retrain
waits 10 minutes after boot so a crash-loop can't burn every restart on it.

### Quality gate
Before predicting, `scan_quality` checks the last 72 bars for gaps,
duplicates, staleness and unsettled bars. A failing scan skips the
prediction and logs an event rather than predicting on bad data.

### Drift watch
Live resolved calls are reduced to **non-overlapping** windows
(`select_independent`) before computing live Brier. Overlapping hourly
calls share 23/24 of their outcome window; treating them as independent
lets drift fire on autocorrelated noise.

### Resolution
For each matured prediction, take **the first bar at or after the
horizon** — the price you would actually have got. Beyond
`_MAX_RESOLUTION_LAG = 4 days` it stays pending, because that silence is a
broken feed rather than a closed market. Before this, any call expiring
into a weekend was orphaned permanently, which biased the surviving record
toward mid-week.

Every prediction records `origin`: `live` or `replay`. Replays are excluded
from every scoreboard by default and badged in the audit log. Replaying a
*trained* model is refused outright — it has already seen those outcomes.

---

## 7. From forecast to trade

```
direction  →  stance
volatility →  stop distance  →  position size  →  management rules
```

**Stance.** Stand aside if direction is neutral, confidence < 0.10, or the
call falls inside the champion's learned abstention band.

**Stop.** `1.5 × expected_move_pips` (`stop_sigma_mult`). A stop inside one
sigma sits where routine noise reaches.

**Target.** `stop × reward_multiple`.

**Size.** `risk_money ÷ (pip_distance × pip_value_per_lot)`, **rounded
down** to the lot step so the budget is never exceeded.

**Guards.** A stop under 3 pips is inside a dealing spread; implied
leverage over 100:1 means the position is arithmetic, not a trade. Both
say so.

**Management**, pre-committed while calm:
- break-even at **1R**
- trail by **1 sigma** of expected move
- bank **50%** at 1R
- **time stop** at the forecast horizon

**Target realism.** At 2:1 with a 1.5σ stop the target is **3 sigma away**,
inside the horizon the time stop closes. And reward:risk cannot create
edge: a driftless walk touches the target first `s/(s+t)` of the time,
algebraically identical to the `1/(1+R)` needed to break even. Both are 33%
at 2:1. The plan states the break-even win rate beside the model's measured
accuracy.

**Event freeze** at the 85th volatility percentile — but it reads the
economic calendar, which needs a Finnhub key that isn't set, so **it
currently cannot fire before scheduled news.**

---

## 8. The statistics layer

Every headline number is passed through the same discipline.

**Independence first.** Collapse overlapping signals to disjoint windows.
In production 92 of 183 resolutions shared a single weekend reopen price —
one market moment counted 92 times.

**Wilson interval**, not the normal approximation, which misbehaves at the
small samples where the question actually gets asked.

**A hard floor: nothing is significant below 30 observations**
(`_MIN_SAMPLE_FOR_VERDICT`). Five correct out of five gives a Wilson lower
bound near 57%, which excludes a coin flip — and happens by chance one time
in thirty-two.

**Sample-size targets are floored at the same 30**, so the app never asks
you to reach a bar that still wouldn't earn a verdict.

The governing arithmetic: at a 24-hour horizon you earn **one independent
observation per trading day**. A thin 53% edge needs ~1,100 of them —
roughly three years. Signal count races ahead and means nothing.

---

## 9. Where it actually stands

Three independent measurements, all pointing the same way:

- The H1 champion **was demoted** — three consecutive fresh re-grades above
  the coin-flip floor. The baseline rule predicts on both lanes.
- **Abstention found nothing.** No confidence band scores better than the
  rest.
- The paper record: **5 independent windows, not distinguishable from a
  coin flip**, ~18 weeks from a verdict.

The one thing that passed its audit is the **volatility forecast**. Use the
system for *how far might this move and where does my stop belong* — not
for which way.

That is not a disappointing result dressed up. It is the system working:
every gate above exists to produce exactly this answer when the answer is
true.

---

## 10. Constants, in one place

| Constant | Value | Where |
|---|---|---|
| `_PROMOTION_MARGIN` | 0.002 | promotion.py |
| `_COIN_FLIP_BRIER` / `_BASELINE_FLOOR` | 0.25 / 0.248 | promotion.py |
| `_DEMOTION_AFTER` | 3 | promotion.py |
| `_SELECTION_FOLDS` | (0.64, 0.80) | promotion.py |
| `MIN_COVERAGE` | 0.15 | selective.py |
| `_MIN_GAIN` | 0.002 | selective.py |
| `_MIN_SAMPLE_FOR_VERDICT` | 30 | significance.py |
| `NORMAL_ONE_SIGMA` | 0.6827 | vol_audit.py |
| `MEAN / MEDIAN_ABS_OVER_SIGMA` | 0.7979 / 0.6745 | vol_audit.py |
| `stop_sigma_mult` | 1.5 | volatility.py |
| `_FREEZE_PCTL` | 0.85 | volatility.py |
| `_RECOMMENDED_RISK_PCT` | 2% | position_sizing.py |
| `_MIN_SENSIBLE_STOP_PIPS` / `_EXTREME_LEVERAGE` | 3 / 100:1 | position_sizing.py |
| `_BREAK_EVEN_R` / `_TRAIL_SIGMA_MULT` / `_PARTIAL_FRACTION` | 1.0 / 1.0 / 0.5 | trade_management.py |
| `_MAX_RESOLUTION_LAG` | 4 days | resolver.py |
| `_MIN_TRADED_WINDOWS` | 2 | walk_forward.py |
| `_QUALITY_WINDOW_BARS` | 72 | scheduler/service.py |
| `loop_train_max_bars` | 6000 | config.py |

---

## 11. What the system will never do

- Execute a trade. Every action is a human's.
- Present a backfill as a track record.
- Call a result significant below 30 independent observations.
- Promote a model that beats the incumbent but not a coin flip.
- Report a check as passed when it did not run.
