"""Forecast value-object invariants."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.forecast import (
    Direction,
    Forecast,
    direction_from_probability,
)
from mentor.domain.market.bars import Timeframe


def _f(p: Decimal = Decimal("0.6")) -> Forecast:
    return Forecast(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        asof=datetime(2026, 6, 25, tzinfo=UTC),
        asof_close=Decimal("1.08500"),
        horizon_bars=24,
        p_up=p,
        confidence=abs(p - Decimal("0.5")) * Decimal("2"),
        direction=direction_from_probability(p),
        model_name="t",
        reasoning="x",
        features={},
    )


def test_rejects_p_out_of_range() -> None:
    with pytest.raises(ValidationError):
        _f(p=Decimal("1.1"))


def test_rejects_naive_ts() -> None:
    with pytest.raises(ValidationError):
        Forecast(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            asof=datetime(2026, 6, 25),
            asof_close=Decimal("1"),
            horizon_bars=24,
            p_up=Decimal("0.5"),
            confidence=Decimal("0"),
            direction=Direction.NEUTRAL,
            model_name="t",
            reasoning="x",
            features={},
        )


def test_direction_from_probability_bands() -> None:
    assert direction_from_probability(Decimal("0.7")) is Direction.LONG
    assert direction_from_probability(Decimal("0.3")) is Direction.SHORT
    assert direction_from_probability(Decimal("0.52")) is Direction.NEUTRAL


def test_zero_neutral_band_excludes_exact_half() -> None:
    assert direction_from_probability(Decimal("0.50"), neutral_band=Decimal("0")) is Direction.LONG
