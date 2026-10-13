"""The back-test gate: says yes to a real edge, no to noise, and cannot be gamed."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mentor.domain.instruments import get_instrument
from mentor.domain.market.bars import Timeframe
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab.gate import (
    HOLDOUT_START,
    _choose,
    _Run,
    collect_evidence,
    grade,
    independent_trades,
)
from mentor.domain.strategy_lab.simulator import ExitReason, Friction, PlanTrade, simulate
from tests.domain.strategy_lab.planted import marker_candidate, planted_market

FRICTION = Friction.for_instrument(get_instrument("EURUSD"))
EDGE = planted_market()
NOISE = planted_market(edge=False, seed=18)


def test_a_real_edge_passes_every_stage() -> None:
    ev = collect_evidence(marker_candidate(), EDGE, FRICTION)
    assert ev.insufficient is None
    assert len(ev.folds) == 4 and all(f.chosen is not None for f in ev.folds)
    v = grade(ev, n_trials=2, dispersion=1.0)
    assert v.passed, v.reasons
    assert v.out_of_sample.n >= 30 and v.out_of_sample.mean > 0.15
    assert v.holdout.n >= 10 and v.holdout.mean > 0


def test_the_same_edge_fails_once_enough_has_been_tried() -> None:
    ev = collect_evidence(marker_candidate(), EDGE, FRICTION)
    v = grade(ev, n_trials=10**6, dispersion=10**4)
    assert not v.passed
    assert any("parameter sets ever tried" in r for r in v.reasons)


def test_noise_is_rejected() -> None:
    v = grade(collect_evidence(marker_candidate(), NOISE, FRICTION), n_trials=2, dispersion=1.0)
    assert not v.passed


def test_every_parameter_set_is_a_trial_on_development_data_only() -> None:
    candidate = marker_candidate()
    ev = collect_evidence(candidate, EDGE, FRICTION)
    assert [t.config_key for t in ev.trials] == [candidate.config_key(s) for s in candidate.specs()]
    holdout = HOLDOUT_START[Timeframe.D1]
    for spec, trial in zip(candidate.specs(), ev.trials, strict=True):
        dev = [t for t in simulate(spec, EDGE, FRICTION).trades if t.exit_ts < holdout]
        assert trial.n_trades == len(dev)


def test_the_held_out_period_is_traded_with_parameters_chosen_before_it() -> None:
    ev = collect_evidence(marker_candidate(), EDGE, FRICTION)
    holdout = HOLDOUT_START[Timeframe.D1]
    assert ev.holdout_trades and all(t.entry_ts >= holdout for t in ev.holdout_trades)
    assert all(t.entry_ts < holdout for t in ev.walk_forward_trades)
    assert ev.final_in_sample is not None and ev.final_params is not None


def test_short_history_is_untestable_but_its_trials_still_count() -> None:
    ev = collect_evidence(marker_candidate(), EDGE.window(len(EDGE) - 200), FRICTION)
    assert ev.insufficient is not None
    assert len(ev.trials) == 2
    v = grade(ev, n_trials=2, dispersion=1.0)
    assert not v.passed and v.reasons[0].startswith("Not enough history")


def _trade(entry: datetime, exit_: datetime, r: float) -> PlanTrade:
    return PlanTrade(
        direction=Direction.LONG,
        signal_ts=entry,
        entry_ts=entry,
        exit_ts=exit_,
        entry_price=1.0,
        exit_price=1.0,
        stop=0.99,
        target=None,
        r=r,
        exit_reason=ExitReason.TIME,
        bars_held=1,
        reason="t",
    )


def test_selection_never_sees_a_trade_that_closed_after_the_test_window_opened() -> None:
    spec = marker_candidate().specs()[0]
    t0 = datetime(2020, 1, 1, tzinfo=UTC)
    test_start = t0 + timedelta(days=100)
    steady = tuple(
        _trade(t0 + timedelta(days=i), t0 + timedelta(days=i, hours=1), 0.1) for i in range(12)
    )
    # The same record plus one enormous winner that only closes inside the test window.
    straddler = (*steady, _trade(t0 + timedelta(days=90), test_start + timedelta(days=5), 50.0))
    honest = _Run(spec, "honest", (*steady[:11], _trade(t0, t0 + timedelta(hours=1), 0.2)))
    leaky = _Run(spec, "leaky", straddler)
    chosen = _choose([leaky, honest], start=t0, end=test_start)
    assert chosen is not None and chosen[1].n_trades == 12
    assert all(r < 1 for r in [chosen[1].mean_r])


def test_a_set_that_lost_in_sample_is_never_chosen() -> None:
    spec = marker_candidate().specs()[0]
    t0 = datetime(2020, 1, 1, tzinfo=UTC)
    losers = tuple(
        _trade(t0 + timedelta(days=i), t0 + timedelta(days=i, hours=1), -0.1) for i in range(20)
    )
    assert _choose([_Run(spec, "x", losers)], start=t0, end=t0 + timedelta(days=50)) is None


def test_overlapping_trades_are_counted_once() -> None:
    t0 = datetime(2020, 1, 1, tzinfo=UTC)
    a = _trade(t0, t0 + timedelta(days=3), 1.0)
    b = _trade(t0 + timedelta(days=1), t0 + timedelta(days=2), 1.0)  # inside a
    c = _trade(t0 + timedelta(days=5), t0 + timedelta(days=6), 1.0)
    kept = independent_trades([a, b, c])
    assert len(kept) == 2 and kept[-1] == c
