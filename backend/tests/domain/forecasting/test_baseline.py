"""Baseline forecaster tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.baseline import BaselineForecaster
from mentor.domain.forecasting.forecast import Direction
from mentor.domain.market.bars import PriceBar, Timeframe


def _series(slope: Decimal, n: int = 250) -> list[PriceBar]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    base = Decimal("1.08")
    return [
        PriceBar(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            ts=start + timedelta(hours=i),
            open=base + Decimal(i) * slope,
            high=base + Decimal(i) * slope + Decimal("0.0010"),
            low=base + Decimal(i) * slope - Decimal("0.0010"),
            close=base + Decimal(i) * slope,
            volume=Decimal("100"),
            source="test",
        )
        for i in range(n)
    ]


def test_baseline_rejects_short_history() -> None:
    fc = BaselineForecaster()
    with pytest.raises(ValidationError):
        fc.forecast(bars=_series(Decimal("0.0001"), n=30), symbol="EURUSD", timeframe=Timeframe.H1)


def test_baseline_leans_long_on_rising_market() -> None:
    fc = BaselineForecaster(horizon_bars=24)
    out = fc.forecast(bars=_series(Decimal("0.0002")), symbol="EURUSD", timeframe=Timeframe.H1)
    assert out.direction is Direction.LONG
    assert out.p_up > Decimal("0.5")
    assert "above the" in out.reasoning


def test_baseline_leans_short_on_falling_market() -> None:
    fc = BaselineForecaster(horizon_bars=24)
    out = fc.forecast(bars=_series(Decimal("-0.0002")), symbol="EURUSD", timeframe=Timeframe.H1)
    assert out.direction is Direction.SHORT
    assert out.p_up < Decimal("0.5")
    assert "below the" in out.reasoning


def test_baseline_caps_probability() -> None:
    fc = BaselineForecaster()
    out = fc.forecast(bars=_series(Decimal("0.0005")), symbol="EURUSD", timeframe=Timeframe.H1)
    assert Decimal("0.30") <= out.p_up <= Decimal("0.70")


def test_baseline_records_features() -> None:
    fc = BaselineForecaster()
    out = fc.forecast(bars=_series(Decimal("0.0002")), symbol="EURUSD", timeframe=Timeframe.H1)
    assert out.features
    assert "rsi_14" in out.features
