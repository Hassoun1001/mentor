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
