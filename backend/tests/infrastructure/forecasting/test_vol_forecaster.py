"""The ML volatility trainer must refuse impossible horizons intelligibly."""

from __future__ import annotations

import math
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.forecasting.sklearn_vol_forecaster import (
    train_sklearn_vol_forecaster,
)


def _bars(n: int = 300) -> list[PriceBar]:
    rng = random.Random(5)
    start = datetime(2024, 1, 1, tzinfo=UTC)
    out: list[PriceBar] = []
    for i in range(n):
        px = 1.10 + 0.01 * math.sin(i / 20) + rng.uniform(-0.002, 0.002)
        p = Decimal(f"{px:.5f}")
        out.append(
            PriceBar(
                symbol="EURUSD",
                timeframe=Timeframe.D1,
                ts=start + timedelta(days=i),
                open=p,
                high=p + Decimal("0.002"),
                low=p - Decimal("0.002"),
                close=p,
                volume=Decimal("1"),
                source="test",
            )
        )
    return out


def test_a_one_bar_horizon_is_refused_with_a_usable_message() -> None:
    """Regression: realized volatility is the spread of returns *inside* the
    horizon, so a one-bar window holds a single return and every label came
    back None. The trainer then failed with "only 0 usable vol samples
    labelled" — true, and useless: it named a symptom the caller cannot act
    on, while the real constraint (and the working alternative) went unsaid.
    Production returned exactly that 400 whenever the ML model was asked for
    a one-day forecast."""
    with pytest.raises(ValidationError) as exc:
        train_sklearn_vol_forecaster(bars=_bars(), horizon_bars=1)
    message = str(exc.value)
    assert "at least 2 bars" in message
    assert "EWMA" in message  # names the alternative that does work


def test_the_smallest_workable_horizon_trains() -> None:
    model = train_sklearn_vol_forecaster(bars=_bars(), horizon_bars=2)
    assert model.report.n_test > 0
