"""Indicator tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.domain.indicators import atr, ema, rsi, sma
from mentor.domain.market.bars import PriceBar, Timeframe


def test_sma_known_value() -> None:
    assert sma([Decimal("1"), Decimal("2"), Decimal("3")], 3) == Decimal("2")


def test_sma_insufficient_returns_none() -> None:
    assert sma([Decimal("1")], 3) is None


def test_ema_seeds_with_sma() -> None:
    # With period 2 and equal values, EMA should equal the values.
    assert ema([Decimal("5"), Decimal("5"), Decimal("5")], 2) == Decimal("5")


def test_atr_minimum_inputs() -> None:
    bars = []
    start = datetime(2026, 1, 1, tzinfo=UTC)
    for i in range(20):
        bars.append(
            PriceBar(
                symbol="EURUSD",
                timeframe=Timeframe.H1,
                ts=start + timedelta(hours=i),
                open=Decimal("1.08"),
                high=Decimal("1.0810"),
                low=Decimal("1.0790"),
                close=Decimal("1.08"),
                volume=Decimal("0"),
                source="test",
            )
        )
    a = atr(bars, period=14)
    assert a is not None
    assert a == Decimal("0.0020")


def test_rsi_all_up_is_100() -> None:
    values = [Decimal(str(1 + i * 0.01)) for i in range(20)]
    assert rsi(values, period=14) == Decimal("100")
