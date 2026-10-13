"""Live verdicts: rationed looks, quick demotion, retirement of losers."""

from __future__ import annotations

import random

from mentor.domain.strategy_lab.live import (
    LabStatus,
    LiveAction,
    checkpoints_reached,
    judge_live,
    next_checkpoint,
)


def _strong(n: int, seed: int = 1) -> list[float]:
    rng = random.Random(seed)
    return [rng.gauss(0.8, 1.0) for _ in range(n)]


def test_nothing_is_judged_before_the_first_checkpoint() -> None:
    d = judge_live(
        status=LabStatus.PAPER, rs=_strong(29), since_promotion=[], looks_taken=0, live_looks_ever=0
    )
    assert d.action is LiveAction.NONE and not d.looked
    assert "next check at 30" in d.reason


def test_a_strong_record_is_promoted_at_the_checkpoint_and_spends_a_look() -> None:
    d = judge_live(
        status=LabStatus.PAPER, rs=_strong(30), since_promotion=[], looks_taken=0, live_looks_ever=0
    )
    assert d.action is LiveAction.PROMOTE and d.status is LabStatus.RECOMMENDED
    assert d.looked and d.looks_taken == 1
    assert d.deflated is not None and d.deflated.n_trials == 1


def test_looks_are_rationed_between_checkpoints() -> None:
    weak = [0.05, -0.05] * 20
    first = judge_live(
        status=LabStatus.PAPER, rs=weak[:30], since_promotion=[], looks_taken=0, live_looks_ever=0
    )
    assert first.action is LiveAction.NONE and first.looks_taken == 1
    for n in range(31, 40):
        d = judge_live(
            status=LabStatus.PAPER,
            rs=weak[:n],
            since_promotion=[],
            looks_taken=1,
            live_looks_ever=1,
        )
        assert not d.looked, "a look between checkpoints would be optional stopping"
    assert checkpoints_reached(59) == 1 and next_checkpoint(1) == 60


def test_other_strategies_looks_raise_the_bar() -> None:
    rng = random.Random(9)
    rs = [rng.gauss(0.45, 1.0) for _ in range(30)]
    alone = judge_live(
        status=LabStatus.PAPER, rs=rs, since_promotion=[], looks_taken=0, live_looks_ever=0
    )
    crowded = judge_live(
        status=LabStatus.PAPER, rs=rs, since_promotion=[], looks_taken=0, live_looks_ever=10_000
    )
    assert alone.deflated is not None and crowded.deflated is not None
    assert crowded.deflated.bar > alone.deflated.bar


def test_recommended_is_demoted_when_trades_since_promotion_average_zero_or_worse() -> None:
    history = _strong(40)
    since = [0.5, -0.5] * 15
    d = judge_live(
        status=LabStatus.RECOMMENDED,
        rs=history + since,
        since_promotion=since,
        looks_taken=1,
        live_looks_ever=1,
    )
    assert d.action is LiveAction.DEMOTE and d.status is LabStatus.DEMOTED


def test_recommended_is_demoted_at_a_checkpoint_that_no_longer_clears() -> None:
    rs = [0.3, -0.3] * 30
    d = judge_live(
        status=LabStatus.RECOMMENDED, rs=rs, since_promotion=[0.1], looks_taken=1, live_looks_ever=1
    )
    assert d.action is LiveAction.DEMOTE and d.looks_taken == 2


def test_a_demoted_plan_can_earn_it_back() -> None:
    d = judge_live(
        status=LabStatus.DEMOTED,
        rs=_strong(60),
        since_promotion=[],
        looks_taken=1,
        live_looks_ever=1,
    )
    assert d.action is LiveAction.PROMOTE


def test_a_significantly_losing_plan_is_retired() -> None:
    rng = random.Random(3)
    rs = [rng.gauss(-0.6, 1.0) for _ in range(35)]
    d = judge_live(
        status=LabStatus.PAPER, rs=rs, since_promotion=[], looks_taken=1, live_looks_ever=1
    )
    assert d.action is LiveAction.RETIRE and d.status is LabStatus.RETIRED


def test_rejected_and_retired_plans_are_not_judged() -> None:
    for status in (LabStatus.REJECTED, LabStatus.RETIRED):
        d = judge_live(
            status=status, rs=_strong(60), since_promotion=[], looks_taken=0, live_looks_ever=0
        )
        assert d.action is LiveAction.NONE and d.status is status
