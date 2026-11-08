"""Playing a saved plan forward: which came first, and when it is final."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.instruments import get_instrument
from mentor.domain.journal.system_plan import (
    PlanSnapshot,
    PlanStance,
    SystemStatus,
    play_forward,
    time_stop_deadline,
)
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.strategy_lab.simulator import ExitReason

EURUSD = get_instrument("EURUSD")
# A Tuesday, so a 24-bar plan stays clear of the weekend.
ASOF = datetime(2026, 11, 3, 8, tzinfo=UTC)
HOUR = timedelta(hours=1)
LONG_AFTER = datetime(2026, 12, 1, tzinfo=UTC)


def _plan(
    stance: PlanStance = PlanStance.LONG,
    asof: datetime = ASOF,
    horizon: int = 24,
) -> PlanSnapshot:
    long = stance is PlanStance.LONG
    return PlanSnapshot(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        asof=asof,
        model_name="champion",
        p_up=Decimal("0.62"),
        confidence=Decimal("0.24"),
        stance=stance,
        horizon_bars=horizon,
        time_stop_deadline=time_stop_deadline(asof, horizon, Timeframe.H1),
        entry=Decimal("1.10000"),
        stop=Decimal("1.09700") if long else Decimal("1.10300"),
        target=Decimal("1.10600") if long else Decimal("1.09400"),
        reward_multiple=Decimal("2"),
    )


def _bar(
    ts: datetime,
    high: str = "1.1005",
    low: str = "1.0995",
    open_: str = "1.1000",
    close: str = "1.1000",
) -> PriceBar:
    return PriceBar(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        ts=ts,
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=None,
        source="test",
    )


def _quiet_bars(n: int, start: datetime = ASOF) -> list[PriceBar]:
    return [_bar(start + HOUR * (i + 1)) for i in range(n)]


def test_stop_reached_first() -> None:
    bars = _quiet_bars(3)
    bars.append(_bar(ASOF + HOUR * 4, low="1.0960", close="1.0970"))
    bars.append(_bar(ASOF + HOUR * 5, high="1.1100", close="1.1090"))

    r = play_forward(_plan(), bars, instrument=EURUSD, now=LONG_AFTER)

    assert r.status is SystemStatus.FINISHED
    assert r.exit_reason is ExitReason.STOP
    # Stop 1.09700, sold 0.6 pips worse.
    assert r.exit_price == Decimal("1.09694")
    # The result is stamped when the deciding bar finished.
    assert r.exit_ts == ASOF + HOUR * 5


def test_target_reached_first() -> None:
    bars = [*_quiet_bars(2), _bar(ASOF + HOUR * 3, high="1.1070", close="1.1065")]

    r = play_forward(_plan(), bars, instrument=EURUSD, now=LONG_AFTER)

    assert r.exit_reason is ExitReason.TARGET
    assert r.exit_price == Decimal("1.10594")
    assert r.exit_ts == ASOF + HOUR * 4


def test_costs_are_charged_on_both_legs_of_the_result() -> None:
    bars = [_bar(ASOF + HOUR, high="1.1070", close="1.1065")]

    r = play_forward(_plan(), bars, instrument=EURUSD, now=LONG_AFTER)

    assert r.entry_price == Decimal("1.10006")  # bought 0.6 pips above the plan
    assert r.pips == Decimal("58.8")  # 60 pips less 1.2 pips of costs
    assert r.r is not None
    # Reward 58.8 pips on a 30.6-pip risk.
    assert Decimal("1.91") < r.r < Decimal("1.93")


def test_time_stop_exits_at_the_close_of_the_last_bar() -> None:
    bars = _quiet_bars(23)
    bars.append(_bar(ASOF + HOUR * 24, close="1.1002"))

    r = play_forward(_plan(), bars, instrument=EURUSD, now=LONG_AFTER)

    assert r.exit_reason is ExitReason.TIME
    assert r.exit_price == Decimal("1.10014")
    assert r.exit_ts == _plan().time_stop_deadline == ASOF + HOUR * 25


def test_when_one_bar_touches_both_the_stop_is_assumed() -> None:
    bars = [_bar(ASOF + HOUR, high="1.1070", low="1.0960", close="1.1000")]

    r = play_forward(_plan(), bars, instrument=EURUSD, now=LONG_AFTER)

    assert r.exit_reason is ExitReason.STOP


def test_a_short_plan_runs_the_other_way() -> None:
    bars = [_bar(ASOF + HOUR, high="1.1035", low="1.0995", close="1.1030")]

    r = play_forward(_plan(PlanStance.SHORT), bars, instrument=EURUSD, now=LONG_AFTER)

    assert r.exit_reason is ExitReason.STOP
    assert r.pips is not None and r.pips < 0


def test_a_gap_through_the_stop_fills_at_the_open() -> None:
    bars = [_bar(ASOF + HOUR, open_="1.0950", high="1.0960", low="1.0940", close="1.0955")]

    r = play_forward(_plan(), bars, instrument=EURUSD, now=LONG_AFTER)

    assert r.exit_reason is ExitReason.STOP
    assert r.exit_price == Decimal("1.09494")


def test_pending_until_the_deadline_bar_has_finished() -> None:
    bars = _quiet_bars(24)
    deadline = _plan().time_stop_deadline

    forming = play_forward(_plan(), bars, instrument=EURUSD, now=deadline - timedelta(minutes=1))
    finished = play_forward(_plan(), bars, instrument=EURUSD, now=deadline)

    assert forming.status is SystemStatus.PENDING
    assert forming.entry_price == Decimal("1.10006")
    assert forming.exit_price is None
    assert finished.status is SystemStatus.FINISHED
    assert finished.exit_reason is ExitReason.TIME


def test_pending_when_there_are_no_bars_yet() -> None:
    r = play_forward(_plan(), [], instrument=EURUSD, now=ASOF + HOUR)
    assert r.status is SystemStatus.PENDING


def test_pending_past_the_deadline_until_the_feed_catches_up() -> None:
    # 20 bars stored, and the clock is past the deadline: the last four bars
    # may still arrive, so calling the time stop now would use the wrong close.
    r = play_forward(_plan(), _quiet_bars(20), instrument=EURUSD, now=LONG_AFTER)
    assert r.status is SystemStatus.PENDING


def test_a_stop_before_the_deadline_is_final_without_waiting() -> None:
    bars = [_bar(ASOF + HOUR, low="1.0960", close="1.0970")]
    r = play_forward(_plan(), bars, instrument=EURUSD, now=ASOF + HOUR * 2)
    assert r.status is SystemStatus.FINISHED
    assert r.exit_reason is ExitReason.STOP


def test_a_bar_still_forming_cannot_decide_anything() -> None:
    bars = [_bar(ASOF + HOUR, low="1.0960", close="1.0970")]
    r = play_forward(_plan(), bars, instrument=EURUSD, now=ASOF + HOUR + timedelta(minutes=30))
    assert r.status is SystemStatus.PENDING


def test_the_plans_own_bar_and_earlier_bars_are_ignored() -> None:
    bars = [_bar(ASOF - HOUR, low="1.0900"), _bar(ASOF, low="1.0900")]
    r = play_forward(_plan(), bars, instrument=EURUSD, now=LONG_AFTER)
    assert r.status is SystemStatus.PENDING


def test_a_missing_deadline_bar_uses_the_last_bar_once_the_feed_has_moved_on() -> None:
    # Bars 1-23 exist, bar 24 never will (a holiday), and bar 26 proves it.
    bars = [*_quiet_bars(22), _bar(ASOF + HOUR * 23, close="1.1004"), _bar(ASOF + HOUR * 26)]

    r = play_forward(_plan(), bars, instrument=EURUSD, now=LONG_AFTER)

    assert r.exit_reason is ExitReason.TIME
    assert r.exit_price == Decimal("1.10034")
    assert r.exit_ts == ASOF + HOUR * 24


def test_stand_aside_plans_have_no_system_trade() -> None:
    plan = PlanSnapshot(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        asof=ASOF,
        model_name="champion",
        p_up=Decimal("0.51"),
        confidence=Decimal("0.02"),
        stance=PlanStance.STAND_ASIDE,
        horizon_bars=24,
        time_stop_deadline=time_stop_deadline(ASOF, 24, Timeframe.H1),
    )
    r = play_forward(plan, _quiet_bars(30), instrument=EURUSD, now=LONG_AFTER)
    assert r.status is SystemStatus.NO_TRADE
    assert r.entry_price is None


# ---- market hours ----

# Friday 20:00 UTC: two tradeable hourly bars before the 22:00 close.
FRIDAY = datetime(2026, 11, 6, 20, tzinfo=UTC)
SUNDAY_OPEN = datetime(2026, 11, 8, 22, tzinfo=UTC)


def test_the_deadline_skips_the_weekend() -> None:
    # One bar on Friday at 21:00, then 23 counted from Sunday's open.
    deadline = time_stop_deadline(FRIDAY, 24, Timeframe.H1)
    assert deadline == SUNDAY_OPEN + HOUR * 23


def test_a_weekend_bar_cannot_hit_the_stop() -> None:
    plan = _plan(asof=FRIDAY)
    saturday = datetime(2026, 11, 7, 12, tzinfo=UTC)
    bars = [_bar(FRIDAY + HOUR), _bar(saturday, low="1.0900", close="1.0950")]

    r = play_forward(plan, bars, instrument=EURUSD, now=LONG_AFTER)

    assert r.status is SystemStatus.PENDING


def test_weekend_bars_do_not_count_towards_the_time_stop() -> None:
    plan = _plan(asof=FRIDAY)
    weekend = [_bar(datetime(2026, 11, 7, h, tzinfo=UTC)) for h in range(24)]
    bars = [_bar(FRIDAY + HOUR), *weekend, *_quiet_bars(22, SUNDAY_OPEN - HOUR)]

    r = play_forward(plan, bars, instrument=EURUSD, now=LONG_AFTER)

    # 1 Friday bar + 22 Sunday-onward bars is 23 of 24, so it has not expired.
    assert r.status is SystemStatus.PENDING

    bars.append(_bar(SUNDAY_OPEN + HOUR * 22, close="1.1003"))
    r = play_forward(plan, bars, instrument=EURUSD, now=LONG_AFTER)

    assert r.exit_reason is ExitReason.TIME
    assert r.exit_ts == plan.time_stop_deadline


def test_a_stop_after_the_reopen_is_counted() -> None:
    plan = _plan(asof=FRIDAY)
    bars = [_bar(SUNDAY_OPEN, open_="1.0950", high="1.0960", low="1.0940", close="1.0955")]

    r = play_forward(plan, bars, instrument=EURUSD, now=LONG_AFTER)

    assert r.exit_reason is ExitReason.STOP
    assert r.exit_price == Decimal("1.09494")  # the gap fills at the open


# ---- the snapshot itself ----


def test_a_saved_plan_cannot_be_edited() -> None:
    plan = _plan()
    with pytest.raises(AttributeError):
        plan.stop = Decimal("1.09")  # type: ignore[misc]


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"stop": Decimal("1.103")}, "stop"),
        ({"target": Decimal("1.09")}, "target"),
        ({"entry": None}, "stance"),
    ],
)
def test_nonsense_levels_are_refused(change: dict[str, Decimal | None], field: str) -> None:
    values: dict[str, object] = {
        "symbol": "EURUSD",
        "timeframe": Timeframe.H1,
        "asof": ASOF,
        "model_name": "champion",
        "p_up": Decimal("0.6"),
        "confidence": Decimal("0.2"),
        "stance": PlanStance.LONG,
        "horizon_bars": 24,
        "time_stop_deadline": ASOF + HOUR * 25,
        "entry": Decimal("1.10"),
        "stop": Decimal("1.097"),
        "target": Decimal("1.106"),
        "reward_multiple": Decimal("2"),
        **change,
    }
    with pytest.raises(ValidationError) as exc:
        PlanSnapshot(**values)  # type: ignore[arg-type]
    assert exc.value.field == field


def test_a_stand_aside_plan_carries_no_levels() -> None:
    with pytest.raises(ValidationError):
        PlanSnapshot(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            asof=ASOF,
            model_name="champion",
            p_up=Decimal("0.5"),
            confidence=Decimal("0"),
            stance=PlanStance.STAND_ASIDE,
            horizon_bars=24,
            time_stop_deadline=ASOF + HOUR * 25,
            entry=Decimal("1.10"),
        )
