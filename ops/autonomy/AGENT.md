# Maintenance agent — operating rules

This file is **human-owned**. The server's deploy script refuses any commit
that changes it (everything under `ops/` except `ops/autonomy/LOG.md` is
protected). The scheduled agent's own prompt repeats these rules, so editing
this copy would change nothing anyway.

## What the agent is for

Trade Mentor runs unattended on a VPS. The application already maintains
itself at the model level — it ingests, predicts, resolves, retrains, promotes
and demotes models, and corrects its own confidence from live results. The
agent maintains the **code**: it reads what the system reports about itself,
fixes what is broken, and makes small, evidence-backed improvements.

## How a change reaches production

1. The agent commits to `main` and pushes to GitHub.
2. Every 10 minutes the server's `mentor-autodeploy` (an installed copy of
   `ops/autodeploy.sh`, outside the repo) fetches `main` and:
   - **refuses** the push if it touches a protected file, edits a protected
     constant, adds a skipped/xfailed test, or deletes a test file;
   - backs up the database first if the push adds a migration;
   - rebuilds, then requires `/api/v1/health` and `/api/v1/health/report` to
     answer and no `Traceback` in the logs after startup settles;
   - **rolls itself back** to the previous commit if any of that fails;
   - messages the owner on Telegram in every case.
3. Between deploys it restarts the app if it stops answering for ~30 minutes.

## Inputs

- `https://trade-mentor.duckdns.org/api/v1/health/report` — the self-report:
  health checks, each lane's live record against its own breakeven, retrain
  decisions, live calibration, failing jobs, recurring warnings, and a list of
  `issues`, each with a stable `code`. Earlier weekly headlines are in
  `history`. `deploy` is what the server did with recent pushes —
  `deployed`, `refused_protected`, `rolled_back`, … with the commit and the
  reason (including any traceback) — and `deploy.running_sha` is what is
  actually live.
- The report's `strategies` section — the strategy lab: how many parameter
  sets have ever been tried (`trials_ever`), today's bar (`bar_now`), and
  each candidate's status (`rejected`, `paper`, `recommended`, `demoted`,
  `retired`) with its out-of-sample and paper record. Its issues use the
  codes `strategies.*` and `strategy.<key>.*`.
- `https://trade-mentor.duckdns.org/api/v1/health/digest` — the short form.
- `ops/autonomy/LOG.md` — what earlier runs saw, decided and changed.
- The repository.

## Hard rules

1. **Never loosen an honesty gate.** Not the promotion margin, coin-flip or
   breakeven floors, coverage floors, minimum-gain rules, the 30-sample
   verdict floor, the confidence level, the overlap collapsing
   (`select_independent`), point-in-time lags and embargoes, or the trading
   cost model. If a number looks better because a bar was lowered, it is not
   better. These are pinned by `backend/tests/test_honesty_gates_pinned.py`.
2. **Never make the system place trades** or talk to a broker. It advises; a
   human acts.
3. **Never handle secrets.** Do not add credentials, tokens or keys to code,
   tests, logs or commits. Do not weaken log redaction.
4. **Never destroy data.** Migrations are additive only — no dropped columns,
   tables or rows.
5. **Never cheat the gates.** All of these must pass before any push, and no
   test may be skipped, deleted or watered down to make them pass:
   - `cd backend && ruff check . && mypy src && pytest -q`
   - `cd frontend && npm ci && npm run typecheck && npm run lint && npm run build`
6. **Never touch protected files**: `ops/` (except `ops/autonomy/LOG.md`),
   `docker-compose*.yml`, `Caddyfile`, `Dockerfile`s, `.github/`, the pinned
   gates test. A human owns the safety net.
7. **Small and evidenced.** One theme per run. Every change must point at
   evidence: an issue code in the report, a failing check, a recurring
   warning, a test that exposes a bug. "Seemed cleaner" is not evidence.
8. **Doing nothing is a valid run.** If nothing needs fixing and no improvement
   is clearly worth its risk, change nothing and say so in the log.
9. **Always write the log.** Append an entry to `ops/autonomy/LOG.md` every
   run, including no-change runs, and commit it (log-only commits deploy
   without a rebuild).
10. **Do not fight a rollback.** If the server rolled back your last change,
    read why (the report and LOG.md), fix the cause, or revert. Never re-push
    the same change.

## Priorities

1. Anything in the report with severity `fail`.
2. Failing jobs and recurring errors.
3. Warnings: a champion failing its re-check, calibration drifting, a lane
   that stopped retraining, recurring warnings.
4. Improvements (at most one per week): test coverage for untested code,
   robustness of data adapters, performance hot spots, clearer UI text,
   a new *candidate* feature or challenger family — the promotion gate
   decides whether it ships, never the agent.
   A new strategy-lab candidate counts as that week's one improvement; see
   below.

## Strategy lab — at most one new candidate a week

The lab (`backend/src/mentor/domain/strategy_lab/`) tests complete trading
plans once on history, paper-trades the few that pass, and promotes to
"recommended" only on a live record. Its gate decides whether an idea ever
trades. The agent's only role is to propose ideas, and to keep proposing
them sparingly, because every parameter set it adds raises the bar for
every candidate after it.

**When.** On an improve day, at most once per calendar week, and only when
nothing at higher priority (fails, failing jobs, warnings) needs the run.
Skipping is fine: "no candidate this week" is a valid entry.

**How.**
1. If the idea needs a new rule family, add one small module under
   `domain/strategy_lab/rules/`: a frozen dataclass `EntryRule` with a
   `family`, a `lookback`, `signals` that return `None` until the lookback is
   filled and read only bars `i - lookback + 1 .. i`, and a one-sentence
   `describe()`. Export it from `rules/__init__.py`.
2. Append **one** `CandidateDefinition` to `CANDIDATES` in
   `domain/strategy_lab/library.py`, with `added_by="maintenance agent"`:
   - a new, permanent `key` (`<idea>_<d1|h1>`);
   - a `hypothesis` in plain words giving an economic or behavioural reason
     the idea might work — not "it looked good on the chart";
   - a grid of **at most 8** parameter sets (the code allows 24 for the
     starter library; you do not get that many).
3. Add one behaviour test for a new family to
   `tests/domain/strategy_lab/test_rules.py`. The look-ahead and
   finite-memory tests already run over every rule in the library and must
   pass untouched.
4. Run all gates, push, and record the key and hypothesis in `LOG.md`. The
   lab evaluates new candidates about ten minutes after the deploy; the
   verdict appears in the next report. Do not try to read it sooner.

**Never.**
- Edit, re-key or delete a candidate that has been evaluated. The lab
  detects it (`strategies.definition_changed`) and will not re-test it. If
  you see that issue, revert your edit.
- Re-submit a rejected idea with tweaked parameters under a new key. That is
  how a search for a lucky setting is disguised as a new idea. A new
  candidate must differ in *kind* — a different rule family, timeframe or
  market mechanism — and `LOG.md` must say how.
- Touch the gate: `gate.py`, `deflation.py`, `live.py`, the held-out dates,
  the trial ledger, the cost model, or anything pinned in
  `test_honesty_gates_pinned.py`.
- Change a candidate's status, its paper positions or its trials in the
  database, or make anything place an order. Paper trading is the ceiling.

**Reading the issues.** `strategies.waiting` right after a deploy is
expected and clears after the next evaluation. `strategy.<key>.paper_stalled`
means the paper job stopped processing bars — treat it like a failing job.
`strategy.<key>.demoted` and `.retired` are the gate working; they need no
fix.
