"""Evaluate registered candidates once, against the whole ledger's bar.

Runs from the scheduler (weekly, and shortly after each boot) and from
the CLI. A candidate is evaluated exactly once: its row in
``strategy_candidates`` is its verdict, and the held-out period has then
been spent on it. Two phases, so every candidate in a batch faces the
same bar:

1. Simulate each pending candidate's whole grid and append every
   parameter set to the trial ledger.
2. Read the ledger's size and dispersion — *after* this batch was added —
   and grade each candidate against that.

A definition that changed after evaluation is not re-tested (that would
spend the held-out period twice); it is reported as
``strategies.definition_changed`` until it is given a new key.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from mentor.application.strategy_lab.store import BarLoader, LabStore
from mentor.domain.instruments import get_instrument
from mentor.domain.market.bars import Timeframe
from mentor.domain.strategy_lab.deflation import TradeStats, trial_dispersion
from mentor.domain.strategy_lab.gate import (
    CandidateEvidence,
    GateVerdict,
    collect_evidence,
    grade,
)
from mentor.domain.strategy_lab.library import CANDIDATES, CandidateDefinition
from mentor.domain.strategy_lab.live import LabStatus
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.simulator import Friction
from mentor.infrastructure.models import (
    StrategyCandidateORM,
    StrategyEventORM,
    StrategyTrialORM,
)
from mentor.logging import get_logger

log = get_logger("mentor.strategy_lab.evaluation")

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class EvaluationOutcome:
    evaluated: tuple[tuple[str, bool], ...]  # (candidate key, passed)
    trials_recorded: int
    trials_ever: int
    changed: tuple[str, ...]

    @property
    def summary(self) -> str:
        if not self.evaluated:
            return f"nothing new to evaluate ({self.trials_ever} trials in the ledger)"
        passed = [k for k, ok in self.evaluated if ok]
        return (
            f"evaluated {len(self.evaluated)} candidate(s), {len(passed)} passed"
            f" ({', '.join(passed) if passed else 'none'}); "
            f"{self.trials_ever} trials in the ledger"
        )


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt is not None else None


def _stats(s: TradeStats) -> dict[str, object]:
    return {
        "n": s.n,
        "mean_r": s.mean,
        "sd_r": s.sd,
        "win_rate": s.win_rate,
        "breakeven_win_rate": s.breakeven_win_rate,
        "score": s.t_adjusted,
    }


def evidence_summary(ev: CandidateEvidence, verdict: GateVerdict) -> dict[str, object]:
    """The verdict and the numbers behind it — aggregates only, no trade list."""
    oos = _stats(verdict.out_of_sample)
    oos["ci_low"] = verdict.expectancy.low
    oos["ci_high"] = verdict.expectancy.high
    return {
        "passed": verdict.passed,
        "reasons": list(verdict.reasons),
        "data": {
            "start": _iso(ev.data_start),
            "holdout_start": _iso(ev.holdout_start),
            "end": _iso(ev.data_end),
            "bars": ev.bars,
        },
        "grid_size": len(ev.trials),
        "n_trials": verdict.deflated.n_trials,
        "dispersion": verdict.deflated.dispersion,
        "null_max": verdict.deflated.null_max,
        "bar": verdict.deflated.bar,
        "score": verdict.deflated.t_adjusted,
        "probability": verdict.deflated.probability,
        "in_sample_mean_r": verdict.in_sample_mean_r,
        "out_of_sample": oos,
        "holdout": _stats(verdict.holdout),
        "folds": [
            {
                "index": f.index,
                "test_start": _iso(f.test_start),
                "test_end": _iso(f.test_end),
                "chosen": f.chosen,
                "trades": f.trades,
                "mean_r": f.mean_r,
            }
            for f in ev.folds
        ],
    }


def _plan(candidate: CandidateDefinition, ev: CandidateEvidence) -> dict[str, object] | None:
    if ev.final_params is None:
        return None
    for spec in candidate.specs():
        if spec.params() == ev.final_params:
            return {
                "config_key": candidate.config_key(spec),
                "params": ev.final_params,
                "plan": spec.describe(),
            }
    return None


def _trial_rows(candidate: CandidateDefinition, ev: CandidateEvidence) -> list[StrategyTrialORM]:
    return [
        StrategyTrialORM(
            config_key=t.config_key,
            candidate_key=candidate.key,
            family=candidate.family,
            timeframe=candidate.timeframe.value,
            params_json=json.dumps(t.params, sort_keys=True),
            n_trades=t.n_trades,
            mean_r=t.mean_r,
            sd_r=t.sd_r,
            t_stat=t.t_stat,
            dev_start=ev.data_start,
            dev_end=ev.holdout_start,
        )
        for t in ev.trials
    ]


class StrategyLabEvaluator:
    def __init__(
        self,
        *,
        store: LabStore,
        load_bars: BarLoader,
        symbol: str,
        candidates: Sequence[CandidateDefinition] = CANDIDATES,
    ) -> None:
        self._store = store
        self._load = load_bars
        self._symbol = symbol
        self._candidates = tuple(candidates)

    async def evaluate_pending(self, *, now: datetime) -> EvaluationOutcome:
        existing = {c.key: c for c in await self._store.list_candidates()}
        changed = tuple(
            c.key
            for c in self._candidates
            if c.key in existing and existing[c.key].fingerprint != c.fingerprint()
        )
        pending = [c for c in self._candidates if c.key not in existing]
        if not pending:
            return EvaluationOutcome((), 0, await self._store.trial_count(), changed)

        series: dict[Timeframe, BarSeries] = {}
        for tf in sorted({c.timeframe for c in pending}):
            series[tf] = await self._load(tf, _EPOCH, now)
        friction = Friction.for_instrument(get_instrument(self._symbol))

        # CPU-bound and pure: keep it off the event loop.
        evidence = await asyncio.to_thread(
            lambda: [collect_evidence(c, series[c.timeframe], friction) for c in pending]
        )

        # Phase 1 — every parameter set of every pending candidate is a trial.
        recorded = await self._store.record_trials(
            [row for c, ev in zip(pending, evidence, strict=True) for row in _trial_rows(c, ev)]
        )
        n_trials = await self._store.trial_count()
        dispersion = trial_dispersion(await self._store.trial_t_stats())

        # Phase 2 — grade everyone against the ledger as it now stands.
        results: list[tuple[str, bool]] = []
        for candidate, ev in zip(pending, evidence, strict=True):
            verdict = grade(ev, n_trials=n_trials, dispersion=dispersion)
            status = LabStatus.PAPER if verdict.passed else LabStatus.REJECTED
            reason = " ".join(verdict.reasons)
            plan = _plan(candidate, ev)
            await self._store.add_candidate(
                StrategyCandidateORM(
                    id=uuid.uuid4(),
                    key=candidate.key,
                    family=candidate.family,
                    timeframe=candidate.timeframe.value,
                    title=candidate.title,
                    hypothesis=candidate.hypothesis,
                    fingerprint=candidate.fingerprint(),
                    status=status.value,
                    status_reason=reason,
                    evaluated_at=now,
                    n_trials_at_evaluation=n_trials,
                    plan_json=json.dumps(plan) if plan is not None else None,
                    evidence_json=json.dumps(evidence_summary(ev, verdict)),
                    paper_started_at=now if verdict.passed else None,
                    last_bar_ts=None,
                    live_looks=0,
                )
            )
            await self._store.add_event(
                StrategyEventORM(
                    id=uuid.uuid4(),
                    candidate_key=candidate.key,
                    kind=status.value,
                    detail=reason,
                    at=now,
                )
            )
            results.append((candidate.key, verdict.passed))
            log.info(
                "strategy_lab.evaluated",
                candidate=candidate.key,
                passed=verdict.passed,
                oos_trades=verdict.out_of_sample.n,
                oos_mean_r=round(verdict.out_of_sample.mean, 4),
                score=round(verdict.deflated.t_adjusted, 3),
                bar=round(verdict.deflated.bar, 3),
            )
        return EvaluationOutcome(tuple(results), recorded, n_trials, changed)
