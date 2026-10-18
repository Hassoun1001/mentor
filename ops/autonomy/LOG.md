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
