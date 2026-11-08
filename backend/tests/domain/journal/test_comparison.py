"""The verdict on a trade against its saved plan, and the totals across trades."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mentor.domain.instruments import get_instrument
from mentor.domain.journal.comparison import (
    MATCH_R_TOLERANCE,
    ActualExit,
    TradeComparison,
    Verdict,
    classify_actual_exit,
    compare_trade,
    summarise,
)
from mentor.domain.journal.system_plan import (
    PlanSnapshot,
    PlanStance,
    SystemResult,
    SystemStatus,
)
from mentor.domain.journal.trade import Trade, TradeStatus
from mentor.domain.market.bars import Timeframe
from mentor.domain.money import Money
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab.simulator import ExitReason

EURUSD = get_instrument("EURUSD")
ASOF = datetime(2026, 11, 3, 8, tzinfo=UTC)
DEADLINE = ASOF + timedelta(hours=25)


def _plan(stance: PlanStance = PlanStance.LONG) -> PlanSnapshot:
    if stance is PlanStance.STAND_ASIDE:
        return PlanSnapshot(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            asof=ASOF,
            model_name="champion",
            p_up=Decimal("0.51"),
            confidence=Decimal("0.02"),
            stance=stance,
            horizon_bars=24,
            time_stop_deadline=DEADLINE,
        )
    long = stance is PlanStance.LONG
    return PlanSnapshot(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        asof=ASOF,
        model_name="champion",
        p_up=Decimal("0.62"),
        confidence=Decimal("0.24"),
        stance=stance,
        horizon_bars=24,
        time_stop_deadline=DEADLINE,
        entry=Decimal("1.1000"),
        stop=Decimal("1.0970") if long else Decimal("1.1030"),
        target=Decimal("1.1060") if long else Decimal("1.0940"),
        reward_multiple=Decimal("2"),
    )


def _system(
    reason: ExitReason = ExitReason.TARGET,
    r: str = "1.92",
    exit_price: str = "1.10594",
    pips: str = "58.8",
    exit_ts: datetime = ASOF + timedelta(hours=6),
) -> SystemResult:
    return SystemResult(
        status=SystemStatus.FINISHED,
        entry_price=Decimal("1.10006"),
        exit_price=Decimal(exit_price),
        exit_reason=reason,
        exit_ts=exit_ts,
        pips=Decimal(pips),
        r=Decimal(r),
    )


PENDING = SystemResult(status=SystemStatus.PENDING, entry_price=Decimal("1.10006"))
NO_TRADE = SystemResult(status=SystemStatus.NO_TRADE)


def _trade(
    direction: Direction = Direction.LONG,
    entry: str = "1.1001",
    exit_price: str = "1.1060",
    r: str = "1.9",
    exit_ts: datetime = ASOF + timedelta(hours=6),
    status: TradeStatus = TradeStatus.CLOSED,
) -> Trade:
    long = direction is Direction.LONG
    closed = status is TradeStatus.CLOSED
    return Trade(
        id=uuid.uuid4(),
        symbol="EURUSD",
        direction=direction,
        status=status,
        size_lots=Decimal("0.3"),
        planned_entry=Decimal("1.1000"),
        planned_stop=Decimal("1.0970") if long else Decimal("1.1030"),
        planned_target=Decimal("1.1060") if long else Decimal("1.0940"),
        initial_risk=Money(Decimal("100"), "USD"),
        reason="following the plan",
        actual_entry=Decimal(entry) if status is not TradeStatus.PLANNED else None,
        actual_exit=Decimal(exit_price) if closed else None,
        entry_ts=ASOF + timedelta(hours=1),
        exit_ts=exit_ts if closed else None,
        realised_r=Decimal(r) if closed else None,
    )


# ---- verdicts ----


def test_match_same_direction_same_exit_and_close_result() -> None:
    c = compare_trade(_trade(), _plan(), _system(), EURUSD)
    assert c.verdict is Verdict.MATCH
    assert "both ended at its target" in c.explanation


def test_match_right_at_the_tolerance_edge() -> None:
    r = str(Decimal("1.92") - MATCH_R_TOLERANCE)
    c = compare_trade(_trade(r=r), _plan(), _system(), EURUSD)
    assert c.verdict is Verdict.MATCH


def test_partial_when_closed_early_by_hand() -> None:
    trade = _trade(exit_price="1.1030", r="0.9", exit_ts=ASOF + timedelta(hours=3))
    c = compare_trade(trade, _plan(), _system(), EURUSD)
    assert c.verdict is Verdict.PARTIAL
    assert c.actual_exit_reason is ActualExit.MANUAL
    assert "about 3h before" in c.explanation
    assert "+0.90R" in c.explanation and "+1.92R" in c.explanation


def test_partial_when_held_past_the_systems_exit() -> None:
    trade = _trade(exit_price="1.1030", r="0.9", exit_ts=ASOF + timedelta(hours=9))
    c = compare_trade(trade, _plan(), _system(), EURUSD)
    assert c.verdict is Verdict.PARTIAL
    assert "about 3h after" in c.explanation


def test_partial_when_the_exits_differ() -> None:
    trade = _trade(exit_price="1.0970", r="-1.0")
    c = compare_trade(trade, _plan(), _system(), EURUSD)
    assert c.verdict is Verdict.PARTIAL
    assert "yours ended at its stop and the system's at its target" in c.explanation


def test_partial_when_the_exit_agrees_but_the_result_does_not() -> None:
    trade = _trade(r="1.5")
    c = compare_trade(trade, _plan(), _system(), EURUSD)
    assert c.verdict is Verdict.PARTIAL
    assert "0.42R worse" in c.explanation


def test_no_match_when_the_direction_is_opposite() -> None:
    trade = _trade(direction=Direction.SHORT, exit_price="1.0940", r="2.0")
    c = compare_trade(trade, _plan(), _system(), EURUSD)
    assert c.verdict is Verdict.NO_MATCH
    assert "said long and this trade went short" in c.explanation
    assert c.entry_slippage_pips is None


def test_no_match_on_opposite_direction_does_not_wait_for_the_system() -> None:
    trade = _trade(direction=Direction.SHORT, exit_price="1.0940", r="2.0")
    c = compare_trade(trade, _plan(), PENDING, EURUSD)
    assert c.verdict is Verdict.NO_MATCH
    assert c.r_difference is None


def test_no_match_when_the_plan_said_stand_aside() -> None:
    c = compare_trade(_trade(r="1.0"), _plan(PlanStance.STAND_ASIDE), NO_TRADE, EURUSD)
    assert c.verdict is Verdict.NO_MATCH
    assert "stand aside" in c.explanation
    # Not trading scored 0R, so the whole result is down to the decision to trade.
    assert c.r_difference == Decimal("1.0")


def test_pending_while_the_system_has_not_finished() -> None:
    c = compare_trade(_trade(), _plan(), PENDING, EURUSD)
    assert c.verdict is Verdict.PENDING
    assert "still running" in c.explanation
    assert c.r_difference is None


@pytest.mark.parametrize("status", [TradeStatus.PLANNED, TradeStatus.OPEN])
def test_no_verdict_until_the_trade_is_closed(status: TradeStatus) -> None:
    c = compare_trade(_trade(status=status), _plan(), _system(), EURUSD)
    assert c.verdict is None
    assert c.actual_r is None


# ---- the numbers ----


def test_entry_slippage_is_positive_when_a_buy_filled_worse() -> None:
    c = compare_trade(_trade(entry="1.1002"), _plan(), _system(), EURUSD)
    assert c.entry_slippage_pips == Decimal("1.4")


def test_entry_slippage_is_negative_when_a_buy_filled_better() -> None:
    c = compare_trade(_trade(entry="1.0999"), _plan(), _system(), EURUSD)
    assert c.entry_slippage_pips == Decimal("-1.6")


def test_entry_slippage_is_positive_when_a_sell_filled_worse() -> None:
    system = replace(_system(), entry_price=Decimal("1.09994"))
    trade = _trade(direction=Direction.SHORT, entry="1.0998", exit_price="1.0940", r="1.9")
    c = compare_trade(trade, _plan(PlanStance.SHORT), system, EURUSD)
    assert c.entry_slippage_pips == Decimal("1.4")


def test_actual_pips_and_r_difference() -> None:
    c = compare_trade(_trade(r="1.5"), _plan(), _system(), EURUSD)
    assert c.actual_pips == Decimal("59.0")
    assert c.r_difference == Decimal("-0.42")


# ---- how the trade ended ----


@pytest.mark.parametrize(
    ("exit_price", "expected"),
    [
        ("1.0970", ActualExit.STOP),
        ("1.0972", ActualExit.STOP),  # filled a little before the level
        ("1.0960", ActualExit.STOP),  # slipped through it
        ("1.1060", ActualExit.TARGET),
        ("1.1058", ActualExit.TARGET),
        ("1.1075", ActualExit.TARGET),
        ("1.1020", ActualExit.MANUAL),
    ],
)
def test_exit_is_read_from_the_trades_own_levels(exit_price: str, expected: ActualExit) -> None:
    assert classify_actual_exit(_trade(exit_price=exit_price), _plan(), EURUSD) is expected


def test_short_exits_are_read_the_right_way_round() -> None:
    plan = _plan(PlanStance.SHORT)
    stop = _trade(direction=Direction.SHORT, exit_price="1.1031")
    target = _trade(direction=Direction.SHORT, exit_price="1.0941")
    assert classify_actual_exit(stop, plan, EURUSD) is ActualExit.STOP
    assert classify_actual_exit(target, plan, EURUSD) is ActualExit.TARGET


def test_closing_around_the_deadline_counts_as_the_time_stop() -> None:
    trade = _trade(exit_price="1.1020", exit_ts=DEADLINE - timedelta(minutes=20))
    assert classify_actual_exit(trade, _plan(), EURUSD) is ActualExit.TIME


def test_closing_long_after_the_deadline_is_not_the_time_stop() -> None:
    trade = _trade(exit_price="1.1020", exit_ts=DEADLINE + timedelta(hours=5))
    assert classify_actual_exit(trade, _plan(), EURUSD) is ActualExit.MANUAL


def test_time_stop_on_both_sides_is_a_match() -> None:
    system = _system(ExitReason.TIME, r="0.65", exit_price="1.1020", pips="19.4", exit_ts=DEADLINE)
    trade = _trade(exit_price="1.1021", r="0.68", exit_ts=DEADLINE + timedelta(minutes=10))
    c = compare_trade(trade, _plan(), system, EURUSD)
    assert c.verdict is Verdict.MATCH


# ---- totals ----


def _compared(actual_r: str, system_r: str) -> TradeComparison:
    return compare_trade(_trade(r=actual_r), _plan(), _system(r=system_r), EURUSD)


def test_summary_counts_each_verdict() -> None:
    comparisons = [
        _compared("1.9", "1.92"),  # match
        compare_trade(_trade(exit_price="1.1030", r="0.9"), _plan(), _system(), EURUSD),  # partial
        compare_trade(_trade(r="1.0"), _plan(PlanStance.STAND_ASIDE), NO_TRADE, EURUSD),  # no match
        compare_trade(_trade(), _plan(), PENDING, EURUSD),  # pending
    ]
    s = summarise(comparisons, unlinked_closed=2)
    assert (s.matches, s.partials, s.no_matches, s.pending) == (1, 1, 1, 1)
    assert s.unlinked == 2
    assert s.compared == 3


def test_summary_totals_cover_the_same_trades_on_both_sides() -> None:
    comparisons = [
        _compared("1.9", "1.92"),
        compare_trade(_trade(exit_price="1.1030", r="0.9"), _plan(), _system(), EURUSD),
        compare_trade(_trade(r="1.0"), _plan(PlanStance.STAND_ASIDE), NO_TRADE, EURUSD),
        compare_trade(_trade(r="5"), _plan(), PENDING, EURUSD),  # must not count
    ]
    s = summarise(comparisons)
    assert s.actual_r == Decimal("3.8")
    assert s.system_r == Decimal("3.84")  # 1.92 + 1.92 + 0 for standing aside
    assert s.execution_r == Decimal("-0.04")
    assert "cost 0.04R" in s.headline


def test_summary_says_so_when_execution_added_to_the_result() -> None:
    s = summarise([_compared("2.5", "1.92")])
    assert s.execution_r == Decimal("0.58")
    assert "added 0.58R" in s.headline


def test_summary_says_when_trades_are_only_waiting_on_the_system() -> None:
    s = summarise([compare_trade(_trade(), _plan(), PENDING, EURUSD)])
    assert s.compared == 0
    assert "1 closed trade is waiting" in s.headline


def test_open_trades_do_not_appear_in_the_summary() -> None:
    open_trade = compare_trade(_trade(status=TradeStatus.OPEN), _plan(), _system(), EURUSD)
    s = summarise([open_trade])
    assert s.compared == 0
    assert (s.matches, s.partials, s.no_matches, s.pending) == (0, 0, 0, 0)
    assert "Nothing to compare yet" in s.headline
