"""PlanBook mechanics: fills, costs, exits, cancellations — and back-test/live equivalence."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

import pytest

from mentor.domain.backtest.costs import CostModel
from mentor.domain.instruments import get_instrument
from mentor.domain.market.bars import Timeframe
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab import indicators
from mentor.domain.strategy_lab.rules import DonchianBreakout, SessionBreakout
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.simulator import (
    Cancelled,
    Closed,
    ExitReason,
    Filled,
    Friction,
    PlanBook,
    PlanTrade,
    Signalled,
    simulate,
)
from mentor.domain.strategy_lab.spec import EntryRule, ExitRules, Signal, StrategySpec
from tests.domain.strategy_lab.fixtures import HOUR, bars, random_walk

FRICTION = Friction.for_instrument(get_instrument("EURUSD"))
COST = 0.00006  # half of 0.8 pips spread + 0.2 pips slippage, in price
FLAT = (1.1000, 1.1010, 1.0990, 1.1000)


@dataclass(frozen=True, slots=True)
class Scripted(EntryRule):
    """Fires exactly the signals it is given, at the bars it is given."""

    family: ClassVar[str] = "scripted"
    script: tuple[tuple[int, Signal], ...] = ()

    @property
    def lookback(self) -> int:
        return 1

    def signals(self, series: BarSeries) -> list[Signal | None]:
        out: list[Signal | None] = [None] * len(series)
        for i, s in self.script:
            if i < len(series):
                out[i] = s
        return out

    def describe(self) -> str:
        return "Scripted signals for testing the simulator's mechanics, nothing more."


def _spec(
    *script: tuple[int, Signal], max_bars: int = 50, target_r: float | None = None
) -> StrategySpec:
    return StrategySpec(
        rule=Scripted(script=tuple(script)),
        exits=ExitRules(stop_atr=2.0, target_r=target_r, max_bars=max_bars, atr_period=1),
        timeframe=Timeframe.D1,
        hypothesis="mechanics test",
    )


def _long(stop: float, target: float | None = None) -> Signal:
    return Signal(Direction.LONG, "test long", stop=stop, target=target)


def test_friction_comes_from_the_pinned_cost_model() -> None:
    assert FRICTION.per_side == pytest.approx(COST)
    assert FRICTION.min_stop == pytest.approx(0.0003)
    wider = Friction.for_instrument(get_instrument("EURUSD"), CostModel(spread_pips=Decimal("2")))
    assert wider.per_side > FRICTION.per_side


def test_fill_at_next_open_with_costs_then_target() -> None:
    series = bars([FLAT, FLAT, (1.1002, 1.1010, 1.0990, 1.1000), (1.1000, 1.1105, 1.0995, 1.1090)])
    result = simulate(_spec((1, _long(1.0950, 1.1100))), series, FRICTION)
    (trade,) = result.trades
    assert trade.entry_ts == series.ts[2]
    assert trade.entry_price == pytest.approx(1.1002 + COST)
    assert trade.exit_reason is ExitReason.TARGET
    assert trade.exit_price == pytest.approx(1.1100 - COST)
    expected_r = (1.1100 - COST - (1.1002 + COST)) / (1.1002 + COST - 1.0950)
    assert trade.r == pytest.approx(expected_r)


def test_stop_wins_when_one_bar_covers_both() -> None:
    series = bars([FLAT, FLAT, FLAT, (1.1000, 1.1200, 1.0900, 1.1000)])
    (trade,) = simulate(_spec((1, _long(1.0950, 1.1100))), series, FRICTION).trades
    assert trade.exit_reason is ExitReason.STOP
    assert trade.r < -1  # a full loss plus costs


def test_gap_through_stop_fills_at_the_open_not_the_stop() -> None:
    series = bars([FLAT, FLAT, FLAT, (1.0900, 1.0910, 1.0880, 1.0900)])
    (trade,) = simulate(_spec((1, _long(1.0950))), series, FRICTION).trades
    assert trade.exit_price == pytest.approx(1.0900 - COST)


def test_gap_past_target_is_credited_only_the_target() -> None:
    series = bars([FLAT, FLAT, FLAT, (1.1200, 1.1210, 1.1190, 1.1200)])
    (trade,) = simulate(_spec((1, _long(1.0950, 1.1100))), series, FRICTION).trades
    assert trade.exit_price == pytest.approx(1.1100 - COST)


def test_time_stop_closes_at_the_close_after_max_bars() -> None:
    series = bars([FLAT, FLAT, FLAT, (1.1000, 1.1010, 1.0990, 1.1005), FLAT])
    (trade,) = simulate(_spec((1, _long(1.0950)), max_bars=2), series, FRICTION).trades
    assert trade.exit_reason is ExitReason.TIME
    assert trade.bars_held == 2
    assert trade.exit_ts == series.ts[3]
    assert trade.exit_price == pytest.approx(1.1005 - COST)


@pytest.mark.parametrize(
    ("next_open", "signal", "why"),
    [
        (1.0940, _long(1.0950), "beyond the stop"),
        (1.0952, _long(1.0950), "too close to the stop"),
        (1.1150, _long(1.0950, 1.1100), "beyond the target"),
    ],
)
def test_a_plan_voided_by_the_open_is_cancelled_not_chased(
    next_open: float, signal: Signal, why: str
) -> None:
    series = bars([FLAT, FLAT, (next_open, next_open + 0.001, next_open - 0.001, next_open)])
    book = PlanBook()
    spec = _spec((1, signal))
    sigs = spec.rule.signals(series)
    atrs = indicators.atr(series.high, series.low, series.close, 1)
    events = [
        e
        for i in range(len(series))
        for e in book.on_bar(
            series, i, signal=sigs[i], atr=atrs[i], exits=spec.exits, friction=FRICTION
        )
    ]
    cancelled = [e for e in events if isinstance(e, Cancelled)]
    assert len(cancelled) == 1 and why in cancelled[0].why
    assert book.open is None and book.pending is None


def test_a_stop_inside_the_spread_is_refused_at_the_signal() -> None:
    series = bars([FLAT, FLAT, FLAT])
    result = simulate(_spec((1, _long(1.0999))), series, FRICTION)
    assert result.trades == () and result.open_trade is None and result.cancelled == 0


def test_one_position_at_a_time() -> None:
    series = bars([FLAT] * 6)
    spec = _spec((1, _long(1.0950)), (2, _long(1.0950)), (3, _long(1.0950)), max_bars=10)
    result = simulate(spec, series, FRICTION)
    assert result.trades == ()
    assert result.open_trade is not None and result.open_trade.signal_ts == series.ts[1]


def test_exit_then_new_signal_on_the_same_bar() -> None:
    series = bars([FLAT, FLAT, FLAT, (1.1000, 1.1010, 1.0940, 1.0960), FLAT, FLAT])
    spec = _spec((1, _long(1.0950)), (3, _long(1.0900)))
    book = PlanBook()
    sigs = spec.rule.signals(series)
    atrs = indicators.atr(series.high, series.low, series.close, 1)
    events = book.on_bar(series, 0, signal=None, atr=None, exits=spec.exits, friction=FRICTION)
    for i in range(1, 4):
        events = book.on_bar(
            series, i, signal=sigs[i], atr=atrs[i], exits=spec.exits, friction=FRICTION
        )
    assert [type(e) for e in events] == [Closed, Signalled]


def test_short_trades_score_the_right_way_round() -> None:
    series = bars([FLAT, FLAT, FLAT, (1.1000, 1.1005, 1.0890, 1.0900)])
    spec = _spec((1, Signal(Direction.SHORT, "test short", stop=1.1050, target=1.0900)))
    (trade,) = simulate(spec, series, FRICTION).trades
    assert trade.exit_reason is ExitReason.TARGET
    assert trade.r > 1


def test_atr_stop_and_r_target_when_the_rule_names_no_levels() -> None:
    series = bars([FLAT, FLAT, FLAT])
    spec = _spec((1, Signal(Direction.LONG, "atr")), target_r=2.0)
    book = PlanBook()
    sigs = spec.rule.signals(series)
    atrs = indicators.atr(series.high, series.low, series.close, 1)
    book.on_bar(series, 0, signal=None, atr=None, exits=spec.exits, friction=FRICTION)
    book.on_bar(series, 1, signal=sigs[1], atr=atrs[1], exits=spec.exits, friction=FRICTION)
    assert book.pending is not None
    atr = atrs[1]
    assert atr is not None
    assert book.pending.stop == pytest.approx(1.1000 - 2 * atr)
    assert book.pending.target == pytest.approx(1.1000 + 2 * (2 * atr))


def _run_in_chunks(spec: StrategySpec, series: BarSeries, chunk: int) -> list[PlanTrade]:
    """Drive a book the way the live paper trader does: a fresh book rebuilt
    from the previous state each run, signals computed only on recent bars."""
    trades: list[PlanTrade] = []
    pending, open_ = None, None
    warm = spec.lookback * 2
    for start in range(0, len(series), chunk):
        end = min(len(series), start + chunk)
        lo = max(0, start - warm)
        window = series.window(lo, end)
        book = PlanBook(pending=pending, open=open_)
        sigs = spec.rule.signals(window)
        atrs = indicators.atr(window.high, window.low, window.close, spec.exits.atr_period)
        for j in range(start - lo, len(window)):
            for e in book.on_bar(
                window, j, signal=sigs[j], atr=atrs[j], exits=spec.exits, friction=FRICTION
            ):
                if isinstance(e, Closed):
                    trades.append(e.trade)
        pending, open_ = book.pending, book.open
    return trades


@pytest.mark.parametrize(
    ("rule", "series"),
    [
        (DonchianBreakout(channel=20), random_walk(700, seed=21)),
        (
            SessionBreakout(range_end_hour=7, session_end_hour=12),
            random_walk(2000, seed=22, step=HOUR, vol=0.0015),
        ),
    ],
)
def test_paper_trading_in_chunks_reproduces_the_backtest_exactly(
    rule: EntryRule, series: BarSeries
) -> None:
    spec = StrategySpec(
        rule=rule,
        exits=ExitRules(stop_atr=2.0, target_r=2.0, max_bars=10),
        timeframe=Timeframe.D1,
        hypothesis="equivalence",
    )
    expected = simulate(spec, series, FRICTION).trades
    assert len(expected) > 5
    for chunk in (1, 7, 50):
        assert _run_in_chunks(spec, series, chunk) == list(expected)


def test_events_are_reported_in_order() -> None:
    series = bars([FLAT, FLAT, (1.1002, 1.1010, 1.0990, 1.1000), (1.1000, 1.1105, 1.0995, 1.1090)])
    spec = _spec((1, _long(1.0950, 1.1100)))
    book = PlanBook()
    sigs = spec.rule.signals(series)
    atrs = indicators.atr(series.high, series.low, series.close, 1)
    kinds = [
        type(e)
        for i in range(len(series))
        for e in book.on_bar(
            series, i, signal=sigs[i], atr=atrs[i], exits=spec.exits, friction=FRICTION
        )
    ]
    assert kinds == [Signalled, Filled, Closed]
