# Maintenance log

Newest entry first. Every run of the maintenance agent appends one entry —
including runs that change nothing. Format:

```
## YYYY-MM-DD — <short title>
- **Report:** status, issue codes seen
- **Decision:** what was done and why (or why nothing was)
- **Change:** commit(s), files, tests added
- **Watch next:** what the next run should check
```

## 2026-10-31 — H1 weekly Brier over the alarm again; model signal, no code change
- **Report:** fetched at 06:36 UTC. Status `warn`, one issue:
  `h1.calibration_week` (warn) — H1 weekly Brier 0.271 over 167 calls
  (prev week 0.187; same alarm fired on 2026-10-17 at 0.270 and cleared
  the week after). No `failing_jobs`, `recurring` empty. Live is
  `ea48e08` (`deployed_docs`), matching `main`; no refusals or rollbacks.
  H1 champion `auto_eurusd_1h_20261006_115233`: 96 independent windows at
  58.3% vs 51.79% breakeven, CI [48.3%, 67.7%], not significant;
  `floor_failures` 0; 6 retrains this week, champion kept (challenger
  0.2451 vs 0.2391 on the same fresh window). Live calibration 23/30. D1
  baseline rule, 16 windows at 50.0% vs 50.72% breakeven; challenger
  0.2576 still misses the 0.248 coin-flip floor. Strategy lab: 74 trials
  ever, bar 4.38, all 8 rejected, nothing waiting or changed. Digest:
  feed, resolution, retrain and alerting all `ok`.
- **Decision:** improve day (Sat), but the warning comes first, and as on
  2026-10-17 it is not a code defect. 167 hourly calls with overlapping
  24-hour windows are about seven independent days, so the weekly Brier
  swings (0.270 → 0.187 → 0.271 over three weeks) while the long-run
  record holds steady at ~58%. Model quality is owned by the system's own
  guards: the fresh-window re-check (passed, 0.2391), demotion on floor
  failures (0), and live calibration once 30 outcomes exist (23 now).
  Raising the alarm or touching the model to clear it would be lowering a
  bar. Per AGENT.md no strategy-lab candidate while a warning is open, and
  no other improvement this week. Checked the gates on untouched `main`
  (Python 3.12, ruff 0.16.9): ruff clean, mypy clean, 816 passed.
- **Change:** this log entry only.
- **Watch next:** if `h1.calibration_week` fires a third time in four
  weeks or `floor_failures` rises, look at whether the champion has gone
  stale (it dates from 2026-10-06), but only through the existing gates.
  Live calibration reaches 30 outcomes in ~7 more; check that its first
  correction applies cleanly. Note for runners: the default `python3` in
  the agent container is 3.11, and the backend needs `python3.12`.

## 2026-10-30 — All clear; no change
- **Report:** fetched at 06:37 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty. Live is `8403e81` (`deployed_docs`),
  matching `main`; no refusals or rollbacks. H1 champion
  `auto_eurusd_1h_20261006_115233`: 95 independent windows at 57.9% vs
  51.79% breakeven, CI [47.8%, 67.3%], not significant; `floor_failures`
  0; weekly Brier 0.259 over 167 calls (prev 0.209); 6 retrains, champion
  kept (challenger 0.2451 vs 0.2391). Live calibration 23/30. D1 baseline
  rule, 16 windows at 50.0% vs 50.72% breakeven, not significant; weekly
  Brier 0.219 (prev 0.211) over 6 calls. Strategy lab: 74 trials ever,
  bar 4.38, all 8 rejected, nothing waiting or changed. Digest: feed,
  resolution, retrain and alerting all `ok`.
- **Decision:** fix day (Fri). No fail/warn issues, failing jobs,
  recurring errors, refusals or rollbacks, so no code change.
- **Change:** this log entry only.
- **Watch next:** H1 weekly Brier jumped to 0.259, worse than a coin flip
  (0.25) this week, though the long-run record is unchanged; watch for
  `h1.champion_failing` or a demotion. Live calibration needs ~7 more
  outcomes to reach 30. Tomorrow (Sat) is the improve day.

## 2026-10-29 — All clear; no change
- **Report:** fetched at 06:37 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty. Live is `0ccc4a7` (`deployed_docs`),
  matching `main`; no refusals or rollbacks. H1 champion
  `auto_eurusd_1h_20261006_115233`: 94 independent windows at 58.5% vs
  51.79% breakeven, CI [48.4%, 67.9%], not significant; `floor_failures`
  0; weekly Brier 0.232 over 169 calls (prev 0.231); 5 retrains, champion
  kept (challenger 0.2538 vs 0.2405). Live calibration 21/30. D1 baseline
  rule, 16 windows at 50.0% vs 50.72% breakeven, not significant; weekly
  Brier 0.240 (prev 0.211) over 6 calls. Strategy lab: 74 trials ever,
  bar 4.38, all 8 rejected, nothing waiting or changed. Digest: feed,
  resolution, retrain and alerting all `ok`.
- **Decision:** fix day (Thu). No fail/warn issues, failing jobs,
  recurring errors, refusals or rollbacks, so no code change.
- **Change:** this log entry only.
- **Watch next:** H1 hit rate recovered (57.0% -> 58.5%); keep watching
  for `h1.champion_failing`. Live calibration reaches the 30-outcome floor
  in ~9 more outcomes. Saturday is the improve day.

## 2026-10-28 — All clear; no change
- **Report:** fetched at 06:37 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty. Live is `2121d6c` (`deployed_docs`),
  matching `main`; no refusals or rollbacks. H1 champion
  `auto_eurusd_1h_20261006_115233`: 93 independent windows at 57.0% vs
  51.79% breakeven, CI [46.8%, 66.6%], not significant; `floor_failures`
  0; weekly Brier 0.236 over 169 calls (prev 0.237); 5 retrains, champion
  kept (challenger 0.2539 vs 0.2388). Live calibration 20/30. D1 baseline
  rule, 15 windows at 46.7% vs 50.72% breakeven, not significant; weekly
  Brier 0.252 (prev 0.216) over 6 calls. Strategy lab: 74 trials ever,
  bar 4.38, all 8 rejected, nothing waiting or changed. Digest: feed,
  resolution, retrain and alerting all `ok`.
- **Decision:** fix day (Wed). No fail/warn issues, failing jobs,
  recurring errors, refusals or rollbacks, so no code change.
- **Change:** this log entry only.
- **Watch next:** H1 hit rate has drifted down for a third day (58.7% ->
  57.0%), CI lower bound now 46.8%; watch for `h1.champion_failing`. D1
  still 46.7% on a tiny sample. Ruff drift may recur with a future release.

## 2026-10-27 — All clear; no change
- **Report:** fetched at 06:36 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty. Live is `def91e1` (`deployed_docs`),
  matching `main`; no refusals or rollbacks. H1 champion
  `auto_eurusd_1h_20261006_115233`: 92 independent windows at 58.7% vs
  51.79% breakeven, CI [48.5%, 68.2%], not significant; `floor_failures`
  0; weekly Brier 0.226 over 170 calls (prev 0.231); 4 retrains, champion
  kept (challenger 0.2578 vs 0.2403). Live calibration 19/30. D1 baseline
  rule, 15 windows at 46.7% vs 50.72% breakeven, not significant; weekly
  Brier 0.240 (prev 0.217) over 6 calls. Strategy lab: 74 trials ever,
  bar 4.38, all 8 rejected, nothing waiting or changed. Digest: feed,
  resolution, retrain and alerting all `ok`.
- **Decision:** fix day (Tue). There are no fail/warn issues, failing
  jobs, recurring errors, refusals or rollbacks, so I made no code change.
- **Change:** this log entry only.
- **Watch next:** H1 CI lower bound is 48.5%, still below breakeven;
  watch for `h1.champion_failing`. D1 hit rate is still 46.7% on a tiny
  sample. Ruff drift may come back with a future release.

## 2026-10-26 — All clear; no change
- **Report:** fetched at 06:36 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty (tally since 2026-10-24 06:52). Live
  is `1ab8e34` (`deployed_docs`), matching `main`; no refusals or
  rollbacks. H1 champion `auto_eurusd_1h_20261006_115233`: 91 independent
  windows at 59.3% vs 51.79% breakeven, CI [49.1%, 68.9%], not
  significant; `floor_failures` 0; weekly Brier 0.233 over 170 calls
  (prev 0.225); 5 retrains, champion kept (challenger 0.2578 vs 0.2403).
  Live calibration 19/30. D1 baseline rule, 15 windows at 46.7% vs
  50.72% breakeven, not significant; weekly Brier 0.262 (prev 0.215) over
  6 calls. Strategy lab: 74 trials ever, bar 4.38, all 8 rejected,
  nothing waiting or changed. Digest: feed, resolution, retrain and
  alerting all `ok`.
- **Decision:** fix day (Mon). No fail/warn issues, failing jobs,
  recurring errors or refusals/rollbacks, so no code change.
- **Change:** this log entry only.
- **Watch next:** H1 CI lower bound (49.1%) is closing on breakeven;
  watch for `h1.champion_failing` either way. D1 hit rate still 46.7% on
  a tiny sample. Ruff drift may recur with a future release.

## 2026-10-25 — All clear; no change
- **Report:** fetched at 06:36 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty. Live is `3f38255` (`deployed`),
  matching `main`, so yesterday's `cfe5283` lint fix deployed with no
  refusal or rollback. H1 champion `auto_eurusd_1h_20261006_115233`: 90
  independent windows at 57.8% vs 51.79% breakeven, CI [47.5%, 67.5%],
  not significant; `floor_failures` 0; weekly Brier 0.211 over 172 calls
  (prev 0.235); 5 retrains, champion kept (challenger 0.2732 vs 0.2391).
  Live calibration 17/30. D1 baseline rule, 15 windows at 46.7% vs 50.72%
  breakeven, not significant; weekly Brier 0.278 (prev 0.208) over 6
  calls. Strategy lab: 74 trials ever, bar 4.38, all 8 rejected, nothing
  waiting or changed. Digest: feed, resolution, retrain and alerting all
  `ok`.
- **Decision:** fix day (Sun). No fail/warn issues, failing jobs,
  recurring errors or refusals/rollbacks, so no code change.
- **Change:** this log entry only.
- **Watch next:** keep an eye on `h1.champion_failing` and the D1 lane
  (hit rate 46.7%, weekly Brier up to 0.278 on a tiny sample). Ruff drift
  may recur with a future release.

## 2026-10-24 — Lint gate fixed for ruff >=0.16 (PLR0917)
- **Report:** fetched at about 06:40 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty. Live is `58a6b43` (`deployed_docs`),
  matching `main`; no refusals or rollbacks. H1 champion
  `auto_eurusd_1h_20261006_115233`: 89 independent windows at 58.4% vs
  51.78% breakeven, CI [48.0%, 68.1%], not significant; `floor_failures`
  0; weekly Brier 0.187 over 225 calls (prev 0.272); 4 retrains, champion
  kept (challenger 0.2549 vs 0.2444). Live calibration 15/30. D1 baseline
  rule, 15 windows at 46.7% vs 50.72% breakeven, not significant.
  Strategy lab: 74 trials ever, bar 4.38, all 8 rejected, nothing waiting
  or changed.
- **Decision:** improve day (Sat), with nothing to fix. I used the week's
  one improvement on the lint-gate drift flagged since 2026-10-20: with
  ruff 0.17.2, which `ruff>=0.7` resolves to today, `ruff check .` fails
  on untouched `main` with 3 PLR0917 errors. I fixed the code instead of
  pinning ruff. No strategy-lab candidate this week.
- **Change:** `cfe5283`. `vol_audit._overall_verdict` and
  `PlanBook._consider` (`strategy_lab/simulator.py`) now take their
  trailing arguments by keyword, like `PlanBook.on_bar`. Their callers
  were updated, and behaviour is unchanged. The `_outcome` helper in
  `tests/domain/tips/test_scoring.py` now takes `*prices` and is typed,
  which removes its `type: ignore`. Gates: ruff 0.17.2 clean, mypy clean,
  816 passed. No test added because nothing behaves differently.
  (`ruff format --check` reports differences that already existed in both
  files; it is not a gate, and I left them alone.)
- **Watch next:** confirm `cfe5283` shows as `deployed` with no rollback.
  A later ruff release may add rules again, and a dev-dep upper bound
  would stop that drift if it recurs. Keep watching `h1.champion_failing`
  and the D1 hit rate (down to 46.7%).

## 2026-10-23 — All clear; no change
- **Report:** fetched at 06:37 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty (tally since 2026-10-20 07:00), so the
  apscheduler max-instances warning is still gone. Live is `d1603f3`
  (`deployed_docs`), matching `main`; no refusals or rollbacks. H1 champion
  `auto_eurusd_1h_20261006_115233`: 88 independent windows at 58.0% vs
  51.78% breakeven, CI [47.5%, 67.7%], not significant; `floor_failures`
  0; weekly Brier 0.209 over 227 calls (prev 0.243); 5 retrains this week,
  champion kept (challenger 0.2549 vs 0.2444). Live calibration 15/30. D1
  baseline rule, 15 windows at 53.3% vs 50.72% breakeven, not significant.
  Strategy lab: 74 trials ever, bar 4.38, all 8 rejected, no
  `strategies.*` issues. Digest: feed, resolution, retrain and alerting
  all `ok`.
- **Decision:** fix day (Fri). No fail/warn issues, failing jobs,
  recurring errors or refusals/rollbacks, so no code change.
- **Change:** this log entry only.
- **Watch next:** the max-instances warning should stay out of
  `recurring`; H1 hit rate recovered to 58.0% and the weekly Brier
  improved, but keep an eye on `h1.champion_failing`. Tomorrow is the
  improve day: the ruff pin / PLR0917 fix is still the first item.

## 2026-10-22 — All clear; no change
- **Report:** fetched at 06:36 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty, so the apscheduler max-instances
  warning has still not come back since the `b8bfa4f` deploy. Live is
  `acde97e` (`deployed_docs`), matching `main`; no refusals or rollbacks.
  H1 champion `auto_eurusd_1h_20261006_115233`: 87 independent windows at
  56.3% vs 51.78% breakeven, CI [45.9%, 66.3%], not significant;
  `floor_failures` 0; weekly Brier 0.231 over 235 calls (prev 0.230,
  down from yesterday's 0.238); 5 retrains this week, champion kept
  (challenger 0.2579 vs 0.2422). Live calibration 14/30. D1 baseline rule,
  15 windows at 53.3% vs 50.71% breakeven, not significant. Strategy lab:
  74 trials ever, bar 4.38, all 8 rejected, no `strategies.*` issues.
  Digest: feed, resolution, retrain and alerting all `ok`.
- **Decision:** fix day (Thu). There are no fail/warn issues, failing jobs,
  recurring errors or refusals/rollbacks, so I made no code change.
- **Change:** this log entry only.
- **Watch next:** `h1.calibration_week` and `h1.champion_failing` (the H1
  hit rate dropped from 58.1% to 56.3% in a day). The max-instances warning
  should stay out of `recurring`. Saturday: the ruff pin / PLR0917 fix is
  still the first improve-day item.

## 2026-10-21 — Max-instances warning gone after the drift-retrain fix; no change
- **Report:** fetched at 06:36 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty (tally since 2026-10-20 07:00, the
  restart after the deploy). So the apscheduler `maximum number of running
  instances` warning has not come back in about 23.5 hours. Live is
  `dcf9a18` (`deployed`, with `b8bfa4f`), matching `main`; no refusals or
  rollbacks. H1 champion `auto_eurusd_1h_20261006_115233`: 86 independent
  windows at 58.1% vs 51.78% breakeven, CI [47.6%, 68.0%], not
  significant; `floor_failures` 0; weekly Brier 0.238 over 262 calls (prev
  0.200); 4 retrains this week, champion kept (challenger 0.2591 vs
  0.2433). Live calibration 12/30. D1 baseline rule, 15 windows at 40.0%
  vs 50.71% breakeven, not significant. Strategy lab: 74 trials ever, bar
  4.38, all 8 rejected, no `strategies.*` issues.
- **Decision:** fix day (Wed) with no fail/warn issues, failing jobs,
  recurring errors or refusals/rollbacks, so no code change. The ruff
  >=0.16 PLR0917 drift from yesterday is a latent gate problem, not a
  report issue, so it waits for an improve day.
- **Change:** this log entry only.
- **Watch next:** the max-instances warning should stay out of `recurring`.
  Also watch for `h1.calibration_week` (the Brier is rising again, 0.238)
  and `h1.champion_failing`. Saturday: the ruff pin / PLR0917 fix is the
  first improve-day item. A strategy-lab candidate is allowed only if
  nothing outranks it.

## 2026-10-20 — Drift retrains no longer stall the resolve job
- **Report:** fetched at 06:37 UTC. Status `warn`, one issue: recurring
  `apscheduler ... skipped: maximum number of running instances reached`
  (12× since 2026-10-14 11:38). No `failing_jobs`; live is `04aecf1`
  (`deployed_docs`), matching `main`; no refusals or rollbacks. H1 champion
  `auto_eurusd_1h_20261006_115233`: 85 independent windows at 58.8% vs
  51.78% breakeven, CI [48.2%, 68.7%], not significant; weekly Brier 0.231
  (prev 0.218); 5 retrains this week, champion kept. Live calibration
  12/30. D1 baseline rule, 15 windows at 53.3%. Strategy lab: 74 trials
  ever, bar 4.38, all 8 rejected.
- **Decision:** fix day (Tue), acting on the warn. The tally keys on the
  template, so the job name isn't in the report, but the code shows it:
  `run_resolve_once` (every 15 min) awaited `_maybe_retrain_on_drift`, which
  ran the roughly hour-long retrain inline. That skips about 4 resolve ticks
  per drift retrain, and 5 H1 retrains in a week against a weekly cadence
  means drift retrains happened. 12 skips fits about 3 of them. Resolution
  also stalled while each one ran.
- **Change:** `b8bfa4f`: when the scheduler is running, the drift retrain
  now runs as its own one-shot `drift_retrain` job, so resolve returns at
  once. On-demand cycles with no scheduler still run it inline. Drift
  thresholds, cooldown and the retrain lock are unchanged. Two regression
  tests in `tests/application/test_scheduler_jobs.py`. Gates: mypy clean,
  816 passed. ruff passes at 0.15.0 but **fails on untouched `main` code
  with ruff >=0.16** (new PLR0917 in `vol_audit.py`, `simulator.py`,
  `test_scoring.py`), because dev deps are unpinned (`ruff>=0.7`).
  Also: `python3` here is 3.11 and the package needs >=3.12, so I used
  `python3.12`.
- **Watch next:** the `maximum number of running instances` warning should
  stop growing after this deploys (the tally resets on restart). If it comes
  back, another job is the cause. Confirm `b8bfa4f` shows as `deployed`.
  The ruff drift needs its own run: pin ruff or fix the 3 PLR0917 sites.

## 2026-10-19 — All clear; no change
- **Report:** fetched at 06:37 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty. Live is `11cf92a` (`deployed_docs`,
  yesterday's log entry), matching `main`; no refusals or rollbacks. H1
  champion `auto_eurusd_1h_20261006_115233`: 84 independent windows at
  58.3% vs 51.77% breakeven, CI [47.7%, 68.3%], not significant;
  `floor_failures` 0; weekly Brier 0.225 over 263 calls (prev 0.228);
  latest retrain kept the champion (challenger 0.3042 vs 0.2452). Live
  calibration 11/30. D1 baseline rule, 14 windows at 50.0%; challenger
  48.9% still under the 50.71% floor. Strategy lab: 74 trials ever, bar
  4.38, no `strategies.*` issues.
- **Decision:** fix day (Mon) with no fail/warn issues, failing jobs,
  recurring errors or refusals/rollbacks, so no code change.
- **Change:** this log entry only.
- **Watch next:** `h1.champion_failing` or a returning
  `h1.calibration_week`; live calibration 11/30; Saturday (new calendar
  week) a strategy-lab candidate is allowed if nothing outranks it.

## 2026-10-18 — H1 calibration warning cleared; all clear, no change
- **Report:** fetched at 06:37 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty. Live is `9e49c52` (`deployed_docs`,
  yesterday's log entry), matching `main`; no refusals or rollbacks. H1
  champion `auto_eurusd_1h_20261006_115233`: 83 independent windows at
  57.8% vs 51.77% breakeven, CI [47.1%, 67.9%], not significant;
  `floor_failures` 0; weekly Brier 0.235 over 263 calls (prev 0.223), back
  under the 0.27 alarm, so `h1.calibration_week` cleared on its own. Live
  calibration 10/30. D1 baseline rule, 14 windows at 50.0%; challenger
  48.9% still under the 50.71% floor. Strategy lab: 8 evaluated, all
  rejected; 74 trials ever, bar 4.38.
- **Decision:** fix day (Sun) with no fail/warn issues, failing jobs,
  recurring errors or refusals/rollbacks, so no code change. Yesterday's
  call holds: the Brier spike was noise over overlapping windows, not a
  defect.
- **Change:** this log entry only.
- **Watch next:** `h1.champion_failing` or a returning
  `h1.calibration_week`; live calibration 10/30; next Saturday (a new
  calendar week) a strategy-lab candidate is allowed if nothing outranks it.

## 2026-10-17 — H1 weekly Brier crossed the alarm; model signal, no code change
- **Report:** fetched at 06:43 UTC. Status `warn`, one issue:
  `h1.calibration_week` (warn) — H1 weekly Brier 0.271 over 210 calls vs
  the 0.27 alarm (prev week 0.228; trend 0.200 → 0.217 → 0.223 → 0.242 →
  0.245 → 0.271 across recent runs). No `failing_jobs`, `recurring` empty.
  Live is `47644ec` (`deployed_docs`), matching `main`; no refusals or
  rollbacks. H1 champion `auto_eurusd_1h_20261006_115233`: 82 independent
  windows at 56.1% vs 51.77% breakeven, CI [45.3%, 66.3%], not
  significant; `floor_failures` 0; latest retrain kept it (challenger
  0.2699 vs champion 0.2447 re-graded on the same fresh window). Live
  calibration 10/30. D1 baseline rule, 14 windows at 50.0%; challenger
  48.9% still under the 50.71% floor. Strategy lab: 8 evaluated, all
  rejected; 74 trials ever, bar 4.38.
- **Decision:** improve day (Sat), but the one warning comes first and it
  is not a code defect. The weekly Brier is a plain mean over 210 hourly
  calls whose 24-hour windows overlap — about five independent days — so
  it is a noisy model-quality signal, and the computation
  (`_brier(_outcome_pairs(week))` in `self_report.py`) is correct. The
  system's own guards own model quality: the fresh-window re-check (the
  champion passed it at 0.2447), demotion after repeated floor failures,
  and live calibration at 30 outcomes. Raising the 0.27 alarm or touching
  the model to clear the warning would be lowering a bar. AGENT.md allows
  a strategy-lab candidate only when no warning needs the run, so none
  this week; no other improvement either, to keep this week's change
  attributable.
- **Change:** this log entry only.
- **Watch next:** whether `h1.calibration_week` persists next week, and
  especially whether the champion starts failing its re-check
  (`h1.champion_failing`) — that is the real signal; live calibration
  10/30; if the warning clears, a strategy candidate is fair game next
  Saturday.

## 2026-10-16 — All clear; no change
- **Report:** fetched at 06:42 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty (none after the dependency-pinning
  deploy). Live is `4748f6a` (`deployed_docs`, yesterday's log entry),
  matching `main`; no refusals or rollbacks. H1 champion
  `auto_eurusd_1h_20261006_115233`: 81 independent windows at 56.8% vs
  51.77% breakeven, CI [45.9%, 67.0%], not significant; weekly Brier 0.242
  (prev 0.245); last challenger (technical) 0.2686 lost to 0.2393. Live
  calibration 8/30. D1 still on the baseline rule (14 windows, 42.9%, was
  57.1%); challenger 48.9% still under the 50.71% floor. Strategy lab: 8
  evaluated, all rejected; 74 trials ever, bar 4.38.
- **Decision:** fix day (Fri) with nothing at fail/warn, so no code change.
  H1 moved 47/80 → 46/81, and D1's rate fell with the window count still
  at 14. Both are expected: `select_independent` walks from the newest
  call backwards, so each new resolved call can re-pick the whole chain of
  kept windows. That is overlap collapsing working as designed, not a
  regression.
- **Change:** this log entry only.
- **Watch next:** first live-calibration check at 30 (8 now); D1 challenger
  vs floors; Saturday is the improve day, and a strategy-lab candidate is
  still allowed this week.

## 2026-10-15 — All clear after four owner deploys; no change
- **Report:** fetched at 06:42 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty. Live is `b295edd` (`deployed`, the
  owner's "Pin every runtime dependency"), matching `main`; the owner's
  `9b9383f`, `77971a1` and `4578b2a` also deployed (one earlier attempt of
  `9b9383f` was `refused_protected` for `ops/autodeploy.sh`, then deployed
  without it). H1 champion `auto_eurusd_1h_20261006_115233`: 80 independent
  windows at 58.8% vs 51.77% breakeven, CI [47.8%, 68.9%], not yet
  significant; weekly Brier 0.223 (prev 0.235). Live calibration 7/30. D1
  still on the baseline rule (14 windows, 57.1%); challenger hit rate 48.9%
  misses the 50.71% floor. Strategy lab: 8 evaluated, all rejected; 74
  trials ever, bar now 4.38.
- **Decision:** fix day (Thu) with no fail/warn issues, failing jobs,
  recurring errors or refusals/rollbacks of agent commits, so no code
  change. The H1 figures are stable since the re-grade: 47/79 → 47/80, one
  new losing window, no silent jump.
- **Change:** this log entry only.
- **Watch next:** first live-calibration check at 30; D1 challenger vs
  floors; any `recurring` warnings after the dependency pinning deploy.

## 2026-10-14 — All clear after the owner's re-grade deploy; no change
- **Report:** fetched at 06:32 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty. Live is `d94ffc2` (`deployed`, the
  owner's "Re-grade graded calls on their own finished bar"); the three
  owner pushes before it (`e284758`, `950244f`, `b8055ab`) also deployed
  cleanly. H1 champion `auto_eurusd_1h_20261006_115233`: 79 independent
  windows at 59.5% vs 51.77% breakeven, CI [48.5%, 69.6%], not yet
  significant; weekly Brier 0.200 (prev 0.254). Live calibration 7/30. D1
  still on the baseline rule (13 windows, 46.2%); its challenger's Brier
  0.260 misses the 0.248 coin-flip floor. Strategy lab: 8 candidates
  evaluated, all rejected; 74 trials ever, bar now 4.38.
- **Decision:** fix day (Wed) with no fail/warn issues, failing jobs,
  recurring errors or deploy refusals/rollbacks, so no code change. Note: the
  H1 win rate moved from 53.2% (yesterday's history) to 59.5% on the same 79
  windows — that is the owner's re-grade onto finished bars, not new
  evidence of skill.
- **Change:** this log entry only.
- **Watch next:** that the re-graded H1 figures stay stable (no further
  silent jumps on an unchanged window count); first live-calibration check at
  30; D1 champion vs floors; GDELT rate-limit warnings in `recurring`.

## 2026-10-13 — Report reachable again, all clear; no change
- **Report:** fetched at 13:14 UTC. Status `ok`, `issues` empty, no
  `failing_jobs`, `recurring` empty. Live is `7094655` (`deployed_docs`); the
  previous push `8c8dd6d` deployed cleanly. H1 champion
  `auto_eurusd_1h_20261006_115233`: 79 independent windows at 55.7% vs 51.79%
  breakeven, CI [44.7%, 66.1%], not yet significant; weekly Brier 0.217 (prev
  0.241). Live calibration 7/30. D1 still on the baseline rule (13 windows,
  46.2%); its challenger misses the coin-flip floor.
- **Decision:** fix day (Tue) with no fail/warn issues, failing jobs or
  recurring errors, so no code change. The earlier "unreachable" entry today
  was a sandbox-egress problem that has since cleared.
- **Change:** this log entry only.
- **Watch next:** H1 independent sample and first live-calibration check;
  whether D1 ever gets a champion past the floors; GDELT rate-limit warnings
  reappearing in `recurring`.

## 2026-10-13 — Report unreachable from the agent sandbox; no change
- **Report:** could not be fetched. `/api/v1/health/report` and `/digest` both
  failed with `CONNECT tunnel failed, response 403`: the agent environment's
  egress proxy denies `trade-mentor.duckdns.org` by network policy. This says
  nothing about the server's own health; the deploy state is unknown to me.
- **Decision:** no code change, as required when the report cannot be read.
  Today is a fix day (Tue) and there is no other evidence to act on.
- **Change:** this log entry only.
- **Watch next:** the owner needs to allow `trade-mentor.duckdns.org` in the
  agent environment's network policy (or switch it to a policy that permits
  it); until then every run is blind and will change nothing.

## 2026-10-13 — Autonomy set up (human)
- **Report:** status OK. H1 champion `auto_eurusd_1h_20261006_115233` live since
  2026-10-06 (58.3% test accuracy vs ~51.8% breakeven); 78 independent H1
  windows at 53.8%, not yet significant. Live calibration 6/30 toward its first
  check. Recurring warning: GDELT rate limiting.
- **Decision:** introduced the self-report, the server auto-deploy with
  refusal/rollback, the pinned honesty gates and this log. Owner chose full
  autonomy with Opus 5.5.
- **Change:** weekly report job (Sat 06:00 UTC) + `/api/v1/health/report`;
  digest now grades only the primary lane against its own breakeven.
- **Watch next:** whether the live champion holds above breakeven as its
  independent sample grows; first live-calibration decision (~late November);
  GDELT rate-limit frequency.
