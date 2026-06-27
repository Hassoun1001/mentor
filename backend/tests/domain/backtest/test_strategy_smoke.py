"""Smoke test: the MA crossover produces trades on a synthetic trending series."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.domain.backtest import CostModel, compute_metrics, run_backtest
from mentor.domain.backtest.strategies import MaCrossover
from mentor.domain.instruments import get_instrument
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.money import Money

EURUSD = get_instrument("EURUSD")


def _v_shape(n: int, slope: Decimal, base: Decimal = Decimal("1.0800")) -> Sequence[PriceBar]:
    """A down-then-up V series.

    A monotonic trend never produces an EMA *crossover* — the fast EMA
    sits on one side of the slow EMA the whole time. To exercise the
    crossover entry we need at least one direction change, so the price
    falls for the first half and rises for the second, guaranteeing a
    genuine fast-crosses-slow event near the turn.
    """
    start = datetime(2026, 1, 1, tzinfo=UTC)
    out: list[PriceBar] = []
    half = n // 2
    for i in range(n):
        offset = (half - i) if i < half else (i - half)
        mid = base + slope * Decimal(offset)
        out.append(
            PriceBar(
                symbol="EURUSD",
                timeframe=Timeframe.H1,
                ts=start + timedelta(hours=i),
                open=mid,
                high=mid + Decimal("0.0010"),
                low=mid - Decimal("0.0010"),
                close=mid,
                volume=Decimal("100"),
                source="test",
            )
        )
    return out


def test_ma_crossover_generates_trades_on_v_shaped_series() -> None:
    # A V-shape (fall then rise) produces a real fast/slow EMA crossover
    # near the turn, which is what triggers the strategy's entry.
    bars = _v_shape(300, slope=Decimal("0.0003"))
    strategy = MaCrossover(instrument=EURUSD, fast_period=10, slow_period=30)
    # Use a per-lot commission so the round-trip cost is reflected in
    # total_costs_paid (spread/slippage are applied to fills, not this field).
    result = run_backtest(
        bars=bars,
        strategy=strategy,
        instrument=EURUSD,
        starting_balance=Money.of("10000", "USD"),
        cost_model=CostModel(commission_per_lot_round_trip=Decimal("5")),
        risk_per_trade_fraction=Decimal("0.01"),
    )
    metrics = compute_metrics(result)
    assert metrics.trade_count >= 1
    assert metrics.total_costs_paid > 0  # commission was charged on the round trip


def test_ma_crossover_makes_no_trade_on_monotonic_trend() -> None:
    # A straight line has no crossover, so a crossover strategy correctly
    # sits out. This documents that "no trade" is the right behaviour, not a bug.
    start = datetime(2026, 1, 1, tzinfo=UTC)
    base = Decimal("1.0800")
    slope = Decimal("0.0002")
    bars = [
        PriceBar(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            ts=start + timedelta(hours=i),
            open=base + slope * Decimal(i),
            high=base + slope * Decimal(i) + Decimal("0.0010"),
            low=base + slope * Decimal(i) - Decimal("0.0010"),
            close=base + slope * Decimal(i),
            volume=Decimal("100"),
            source="test",
        )
        for i in range(300)
    ]
    result = run_backtest(
        bars=bars,
        strategy=MaCrossover(instrument=EURUSD, fast_period=10, slow_period=30),
        instrument=EURUSD,
        starting_balance=Money.of("10000", "USD"),
        cost_model=CostModel(),
        risk_per_trade_fraction=Decimal("0.01"),
    )
    assert compute_metrics(result).trade_count == 0
