"""The back-test gate: does an idea survive history, honestly tested?

A candidate is judged as a *procedure* — "trade this rule family, choosing
its parameters from what you have seen so far" — because that is the only
thing anyone could actually have done. Concretely:

1. **Every parameter set is simulated once** over all the bars, with full
   costs. The simulator is causal, so the trades a parameter set made in
   any window are exactly what it would have done trading live through it.
2. **Every parameter set is a trial.** Its record on the development
   period (everything before the held-out start) goes into the append-only
   ledger, chosen or not.
3. **Walk-forward.** The development period is cut into
   ``_WALK_FORWARD_FOLDS + 1`` blocks. For each later block the parameters
   are chosen on all earlier blocks — the set with the best t-statistic
   among those with at least ``_MIN_SELECTION_TRADES`` trades and a
   positive average (a trader does not run a plan that lost in testing) —
   and graded on that block. Training trades must have *closed* before the
   test block starts, so no outcome from the future leaks into a choice.
4. **The held-out period** (``_HOLDOUT_START_*`` onward, pinned) is
   touched once: parameters chosen on the whole development period, then
   traded through it.
5. **The verdict** pools every out-of-sample trade — walk-forward blocks
   plus the held-out period — reduces it to trades that do not overlap in
   market time, and requires all of:
   - at least ``MIN_SAMPLE_FOR_VERDICT`` (30) of them;
   - an average R whose 95% interval is above zero (``assess_expectancy``);
   - a t-statistic above the deflated bar for *every trial ever recorded*;
   - the held-out period on its own: at least ``_HOLDOUT_MIN_TRADES``
     trades and a positive average.

Breakeven here is zero R: costs are already inside every R-multiple. The
win rate the payoff shape needs is reported beside the real one, because
that is the version of "breakeven" a person can check by eye.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Final

from mentor.domain.market.bars import Timeframe
from mentor.domain.stats.independence import select_independent
from mentor.domain.stats.significance import (
    MIN_SAMPLE_FOR_VERDICT,
    MeanVerdict,
    assess_expectancy,
)
from mentor.domain.strategy_lab.deflation import (
    DeflatedVerdict,
    TradeStats,
    deflate,
    trade_stats,
)
from mentor.domain.strategy_lab.library import CandidateDefinition
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.simulator import Friction, PlanTrade, simulate
from mentor.domain.strategy_lab.spec import ParamValue, StrategySpec

# ---- pinned gate constants (see tests/test_honesty_gates_pinned.py) ----------
# Development blocks after the first, each graded on parameters chosen before it.
_WALK_FORWARD_FOLDS = 4
# A parameter set with fewer in-sample trades than this cannot be chosen.
_MIN_SELECTION_TRADES = 10
# The held-out period must confirm on at least this many trades of its own.
_HOLDOUT_MIN_TRADES = 10
# Where history stops being development data. Fixed dates, so the held-out
# stretch cannot be slid around until a candidate looks good on it.
_HOLDOUT_START_D1 = datetime(2024, 1, 1, tzinfo=UTC)
_HOLDOUT_START_H1 = datetime(2026, 4, 1, tzinfo=UTC)

HOLDOUT_START: Final[dict[Timeframe, datetime]] = {
    Timeframe.D1: _HOLDOUT_START_D1,
    Timeframe.H1: _HOLDOUT_START_H1,
}

# Each development block must be at least one full lookback long, or the
# first fold would be nothing but warm-up. Shorter blocks would not flatter
# anything — a fold with too little data simply stands aside — but a
# candidate that can never trade a fold is untestable, and says so.
_MIN_LOOKBACKS_PER_BLOCK = 1


@dataclass(frozen=True, slots=True)
class TrialRecord:
    """One parameter set's development-period record — a ledger row."""

    config_key: str
    params: dict[str, ParamValue]
    n_trades: int
    mean_r: float
    sd_r: float
    t_stat: float


@dataclass(frozen=True, slots=True)
class FoldRecord:
    index: int
    test_start: datetime
    test_end: datetime
    chosen: dict[str, ParamValue] | None  # None: nothing qualified, so it stood aside
    in_sample_t: float | None
    trades: int
    mean_r: float | None


@dataclass(frozen=True, slots=True)
class CandidateEvidence:
    key: str
    timeframe: Timeframe
    data_start: datetime | None
    holdout_start: datetime
    data_end: datetime | None
    bars: int
    trials: tuple[TrialRecord, ...]
    folds: tuple[FoldRecord, ...]
    walk_forward_trades: tuple[PlanTrade, ...]
    final_params: dict[str, ParamValue] | None
    final_in_sample: TrialRecord | None
    holdout_trades: tuple[PlanTrade, ...]
    insufficient: str | None = None  # why the candidate could not be tested at all


@dataclass(frozen=True, slots=True)
class _Run:
    spec: StrategySpec
    config_key: str
    trades: tuple[PlanTrade, ...]


def _window(
    trades: Sequence[PlanTrade], *, entry_from: datetime, closed_by: datetime
) -> list[float]:
    return [t.r for t in trades if t.entry_ts >= entry_from and t.exit_ts < closed_by]


def _record(run: _Run, rs: Sequence[float]) -> TrialRecord:
    s = trade_stats(rs)
    return TrialRecord(
        config_key=run.config_key,
        params=run.spec.params(),
        n_trades=s.n,
        mean_r=s.mean,
        sd_r=s.sd,
        t_stat=s.t_stat,
    )


def _choose(
    runs: Sequence[_Run], *, start: datetime, end: datetime
) -> tuple[_Run, TrialRecord] | None:
    best: tuple[_Run, TrialRecord] | None = None
    for run in runs:
        rec = _record(run, _window(run.trades, entry_from=start, closed_by=end))
        if rec.n_trades < _MIN_SELECTION_TRADES or rec.mean_r <= 0:
            continue
        if best is None or rec.t_stat > best[1].t_stat:
            best = (run, rec)
    return best


def collect_evidence(
    candidate: CandidateDefinition, series: BarSeries, friction: Friction
) -> CandidateEvidence:
    """Simulate every parameter set and assemble the out-of-sample record. Pure."""
    holdout_start = HOLDOUT_START[candidate.timeframe]
    specs = candidate.specs()
    runs = [
        _Run(s, candidate.config_key(s), simulate(s, series, friction).trades)
        for s in specs
    ]
    data_start = series.ts[0] if len(series) else None
    data_end = series.ts[-1] if len(series) else None
    dev_bars = series.index_at_or_after(holdout_start)
    needed = (_WALK_FORWARD_FOLDS + 1) * _MIN_LOOKBACKS_PER_BLOCK * max(s.lookback for s in specs)

    # Every parameter set is a trial, recorded even when the data turns out short.
    trials = tuple(
        _record(r, _window(r.trades, entry_from=data_start, closed_by=holdout_start))
        if data_start is not None
        else _record(r, [])
        for r in runs
    )
    empty = CandidateEvidence(
        key=candidate.key,
        timeframe=candidate.timeframe,
        data_start=data_start,
        holdout_start=holdout_start,
        data_end=data_end,
        bars=len(series),
        trials=trials,
        folds=(),
        walk_forward_trades=(),
        final_params=None,
        final_in_sample=None,
        holdout_trades=(),
    )
    if data_start is None or dev_bars < needed or dev_bars >= len(series):
        why = (
            f"only {dev_bars} development bars before {holdout_start:%Y-%m-%d} "
            f"(needs {needed}) and {len(series) - dev_bars} held-out bars"
        )
        return replace(empty, insufficient=why)

    block = dev_bars // (_WALK_FORWARD_FOLDS + 1)
    edges = [series.ts[k * block] for k in range(1, _WALK_FORWARD_FOLDS + 1)] + [holdout_start]
    folds: list[FoldRecord] = []
    wf_trades: list[PlanTrade] = []
    for k in range(_WALK_FORWARD_FOLDS):
        test_start, test_end = edges[k], edges[k + 1]
        chosen = _choose(runs, start=data_start, end=test_start)
        oos = (
            [t for t in chosen[0].trades if test_start <= t.entry_ts < test_end]
            if chosen is not None
            else []
        )
        wf_trades += oos
        oos_stats = trade_stats([t.r for t in oos])
        folds.append(
            FoldRecord(
                index=k + 1,
                test_start=test_start,
                test_end=test_end,
                chosen=chosen[0].spec.params() if chosen is not None else None,
                in_sample_t=chosen[1].t_stat if chosen is not None else None,
                trades=len(oos),
                mean_r=oos_stats.mean if oos else None,
            )
        )

    final = _choose(runs, start=data_start, end=holdout_start)
    holdout = (
        tuple(t for t in final[0].trades if t.entry_ts >= holdout_start)
        if final is not None
        else ()
    )
    return replace(
        empty,
        folds=tuple(folds),
        walk_forward_trades=tuple(wf_trades),
        final_params=final[0].spec.params() if final is not None else None,
        final_in_sample=final[1] if final is not None else None,
        holdout_trades=holdout,
    )


def independent_trades(trades: Sequence[PlanTrade]) -> list[PlanTrade]:
    """Drop trades that overlap a later one in market time (newest kept)."""
    kept = select_independent([(t.entry_ts, t.exit_ts, t.r, i) for i, t in enumerate(trades)])
    return sorted((trades[i] for _, i in kept), key=lambda t: t.entry_ts)


@dataclass(frozen=True, slots=True)
class GateVerdict:
    passed: bool
    reasons: tuple[str, ...]
    out_of_sample: TradeStats
    expectancy: MeanVerdict
    deflated: DeflatedVerdict
    holdout: TradeStats
    in_sample_mean_r: float | None


def grade(evidence: CandidateEvidence, *, n_trials: int, dispersion: float) -> GateVerdict:
    """Apply the gate to a candidate's evidence, given the whole ledger's size."""
    pooled = independent_trades([*evidence.walk_forward_trades, *evidence.holdout_trades])
    rs = [t.r for t in pooled]
    oos = trade_stats(rs)
    expectancy = assess_expectancy(rs, label="out-of-sample trades")
    deflated = deflate(oos, n_trials=n_trials, dispersion=dispersion)
    holdout = trade_stats([t.r for t in evidence.holdout_trades])
    in_sample = evidence.final_in_sample.mean_r if evidence.final_in_sample else None

    reasons: list[str] = []
    if evidence.insufficient is not None:
        reasons.append(f"Not enough history to test it: {evidence.insufficient}.")
    if oos.n < MIN_SAMPLE_FOR_VERDICT:
        reasons.append(
            f"Only {oos.n} out-of-sample trades; nothing is judged on fewer than "
            f"{MIN_SAMPLE_FOR_VERDICT}."
        )
    elif not (expectancy.significant and expectancy.mean > 0):
        reasons.append(
            f"Out-of-sample trades averaged {expectancy.mean:+.2f}R after costs; the 95% "
            f"range [{expectancy.low:+.2f}R, {expectancy.high:+.2f}R] does not clear zero."
        )
    if oos.n >= MIN_SAMPLE_FOR_VERDICT and not deflated.passed:
        reasons.append(
            f"After allowing for all {n_trials} parameter sets ever tried, the evidence "
            f"needed a score of {deflated.bar:.2f}; it scored {deflated.t_adjusted:.2f}."
        )
    if evidence.insufficient is None:
        if evidence.final_params is None:
            reasons.append("No parameter set earned a place on the development data.")
        elif holdout.n < _HOLDOUT_MIN_TRADES:
            reasons.append(
                f"The held-out period produced only {holdout.n} trades; it needs "
                f"{_HOLDOUT_MIN_TRADES} to confirm anything."
            )
        elif holdout.mean <= 0:
            reasons.append(
                f"The held-out period, untouched until now, averaged {holdout.mean:+.2f}R "
                f"over {holdout.n} trades — it did not confirm."
            )

    passed = not reasons
    if passed:
        reasons.append(
            f"{oos.n} out-of-sample trades averaging {oos.mean:+.2f}R after costs, scoring "
            f"{deflated.t_adjusted:.2f} against a bar of {deflated.bar:.2f} for "
            f"{n_trials} trials, and the held-out period confirmed ({holdout.mean:+.2f}R "
            f"over {holdout.n} trades)."
        )
    return GateVerdict(
        passed=passed,
        reasons=tuple(reasons),
        out_of_sample=oos,
        expectancy=expectancy,
        deflated=deflated,
        holdout=holdout,
        in_sample_mean_r=in_sample,
    )
