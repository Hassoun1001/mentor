"""Engine ordering + cost-aware fill tests."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.domain.backtest import CostModel, run_backtest
from mentor.domain.backtest.orders import ExitReason, OrderIntent
from mentor.domain.backtest.strategy import Strategy, StrategyContext
from mentor.domain.backtest.walk_forward import WalkForwardResult
from mentor.domain.instruments import get_instrument
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.money import Money
from mentor.domain.risk.position_sizing import Direction

EURUSD = get_instrument("EURUSD")


def _series(prices: Sequence[Decimal]) -> list[PriceBar]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    out: list[PriceBar] = []
    for i, p in enumerate(prices):
        out.append(
            PriceBar(
                symbol="EURUSD",
                timeframe=Timeframe.H1,
                ts=start + timedelta(hours=i),
                open=p,
                high=p + Decimal("0.0005"),
                low=p - Decimal("0.0005"),
                close=p,
                volume=Decimal("100"),
                source="test",
            )
        )
    return out


@dataclass(frozen=True, slots=True)
class _LongOnBarOne(Strategy):
    stop: Decimal
    target: Decimal | None
    lots: Decimal = Decimal("0.10")

    @property
    def name(self) -> str:
        return "fixture_long_on_bar_one"

    def on_bar(self, ctx: StrategyContext) -> list[OrderIntent]:
        if ctx.state.get("fired") or ctx.view.visible_count != 1:
            return []
        ctx.state["fired"] = True
        return [
            OrderIntent(
                direction=Direction.LONG,
                size_lots=self.lots,
                stop_price=self.stop,
                target_price=self.target,
                reason="fixture",
            )
        ]


def test_intent_fills_on_next_bar_open_not_current_close() -> None:
    bars = _series([Decimal("1.0800"), Decimal("1.0900"), Decimal("1.0950")])
    # Strategy fires on bar 0 (close = 1.0800). Engine fills at bar 1's open = 1.0900.
    result = run_backtest(
        bars=bars,
        strategy=_LongOnBarOne(stop=Decimal("1.05"), target=None),
        instrument=EURUSD,
        starting_balance=Money.of("10000", "USD"),
        cost_model=CostModel(spread_pips=Decimal("0"), slippage_pips=Decimal("0")),
    )
    # End-of-data forces a close at the last bar's close.
    assert len(result.closed_trades) == 1
    trade = result.closed_trades[0]
    assert trade.entry_price == Decimal("1.0900")  # filled at bar 1 open, not bar 0 close
    assert trade.exit_reason is ExitReason.END_OF_DATA


def test_costs_widen_the_entry_fill_for_a_long() -> None:
    bars = _series([Decimal("1.0800"), Decimal("1.0900"), Decimal("1.0850")])
    costs = CostModel(spread_pips=Decimal("2"), slippage_pips=Decimal("1"))
    # Half spread + slippage = 1 + 1 = 2 pips = 0.0002
    result = run_backtest(
        bars=bars,
        strategy=_LongOnBarOne(stop=Decimal("1.05"), target=None),
        instrument=EURUSD,
        starting_balance=Money.of("10000", "USD"),
        cost_model=costs,
    )
    assert len(result.closed_trades) == 1
    assert result.closed_trades[0].entry_price == Decimal("1.0902")  # 1.09 + 0.0002


def test_stop_hit_within_bar_range() -> None:
    @dataclass(frozen=True, slots=True)
    class _LongAtOpen(Strategy):
        @property
        def name(self) -> str:
            return "long_then_stop_hits"

        def on_bar(self, ctx: StrategyContext) -> list[OrderIntent]:
            if ctx.state.get("fired"):
                return []
            ctx.state["fired"] = True
            return [
                OrderIntent(
                    direction=Direction.LONG,
                    size_lots=Decimal("0.10"),
                    stop_price=Decimal("1.0750"),
                    target_price=Decimal("1.1000"),
                    reason="x",
                )
            ]

    bars = [
        PriceBar(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            ts=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=i),
            open=o,
            high=h,
            low=lo,
            close=c,
            volume=Decimal("100"),
            source="test",
        )
        for i, (o, h, lo, c) in enumerate(
            [
                (Decimal("1.0800"), Decimal("1.0810"), Decimal("1.0795"), Decimal("1.0805")),
                (Decimal("1.0805"), Decimal("1.0820"), Decimal("1.0700"), Decimal("1.0710")),
            ]
        )
    ]
    # Strategy fires on bar 0; bar 1 fills at open 1.0805 and that same bar
    # has low 1.0700 < stop 1.0750 → stop hits.
    result = run_backtest(
        bars=bars,
        strategy=_LongAtOpen(),
        instrument=EURUSD,
        starting_balance=Money.of("10000", "USD"),
        cost_model=CostModel(spread_pips=Decimal("0"), slippage_pips=Decimal("0")),
    )
    assert len(result.closed_trades) == 1
    trade = result.closed_trades[0]
    assert trade.exit_reason is ExitReason.STOP
    assert trade.exit_price == Decimal("1.0750")
    assert trade.realised_r < 0


# ---------- cost reporting ----------


def test_reported_costs_include_the_friction_actually_charged() -> None:
    """Regression: spread and slippage are taken out of the fill prices, but
    `total_costs_paid` accumulated commission only — which defaults to zero.
    A production run of 25 trades reported "total costs paid: 0.00" while
    charging 1.2 pips of friction on every round trip. The number told the
    reader the opposite of the truth."""
    instrument = get_instrument("EURUSD")
    model = CostModel(
        spread_pips=Decimal("0.8"),
        slippage_pips=Decimal("0.2"),
        commission_per_lot_round_trip=Decimal("0"),
    )

    # 0.8 spread + 2 x 0.2 slippage = 1.2 pips per round trip.
    friction = model.friction_for(Decimal("1.0"), instrument)
    expected = Decimal("1.2") * instrument.pip_size * instrument.contract_size

    assert friction == expected
    assert friction > 0  # the whole point: never silently zero
    assert model.commission_for(Decimal("1.0")) == Decimal("0")


# ---------- walk-forward: empty windows are not results ----------


def test_empty_windows_do_not_contribute_to_the_out_of_sample_average() -> None:
    """Regression: every window was averaged in regardless of trade count, so
    a window that never traded contributed an expectancy of zero as though it
    were a measurement. A production run had 3 of 4 test windows empty; those
    zeros dragged the out-of-sample average down and inflated the degradation
    figure that drives the "possible overfit" warning."""
    # Two traded windows in-sample, one out — below the conclusive bar.
    thin = WalkForwardResult(
        windows=(),
        in_sample_avg_expectancy_r=Decimal("0.4"),
        out_of_sample_avg_expectancy_r=Decimal("0.0"),
        degradation_pct=Decimal("100"),
        final_test_metrics=None,
        traded_in_sample_windows=2,
        traded_out_of_sample_windows=1,
    )
    assert not thin.conclusive
    assert not thin.is_overfit_signal  # would have fired on 100% degradation

    solid = WalkForwardResult(
        windows=(),
        in_sample_avg_expectancy_r=Decimal("0.4"),
        out_of_sample_avg_expectancy_r=Decimal("0.0"),
        degradation_pct=Decimal("100"),
        final_test_metrics=None,
        traded_in_sample_windows=3,
        traded_out_of_sample_windows=3,
    )
    assert solid.conclusive
    assert solid.is_overfit_signal  # a real degradation still flags
