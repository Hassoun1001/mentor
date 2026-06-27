"""Walk-forward harness smoke test."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.domain.backtest import walk_forward
from mentor.domain.backtest.strategies import BuyAndHold
from mentor.domain.instruments import get_instrument
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.money import Money

EURUSD = get_instrument("EURUSD")


def test_walk_forward_yields_n_windows() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    bars = [
        PriceBar(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            ts=start + timedelta(hours=i),
            open=Decimal("1.0800") + Decimal(i) * Decimal("0.0001"),
            high=Decimal("1.0810") + Decimal(i) * Decimal("0.0001"),
            low=Decimal("1.0790") + Decimal(i) * Decimal("0.0001"),
            close=Decimal("1.0805") + Decimal(i) * Decimal("0.0001"),
            volume=Decimal("100"),
            source="test",
        )
        for i in range(400)
    ]
    result = walk_forward(
        bars=bars,
        instrument=EURUSD,
        strategy_factory=lambda: BuyAndHold(instrument=EURUSD),
        starting_balance=Money.of("10000", "USD"),
        n_windows=4,
    )
    assert len(result.windows) == 4
    for w in result.windows:
        assert w.train_bars > 0
        assert w.test_bars > 0
