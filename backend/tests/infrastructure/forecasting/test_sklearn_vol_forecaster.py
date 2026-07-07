"""Vol regressor smoke test — trains, grades vs EWMA, forecasts a range."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.macro_features import MACRO_FEATURE_NAMES
from mentor.domain.forecasting.vol_features import VOL_FEATURE_NAMES
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.forecasting.sklearn_vol_forecaster import (
    train_sklearn_vol_forecaster,
)


def _clustered_bars(n: int) -> list[PriceBar]:
    """Synthetic series with volatility clustering (calm/volatile regimes)."""
    start = datetime(2020, 1, 1, tzinfo=UTC)
    price = 1.10
    bars: list[PriceBar] = []
    for i in range(n):
        # Regime flips every ~40 bars: alternately calm and volatile.
        amp = 0.0004 if (i // 40) % 2 == 0 else 0.0025
        step = amp * math.sin(i * 1.7) + amp * 0.5 * math.cos(i * 0.9)
        price = max(0.5, price + step)
        p = Decimal(str(round(price, 6)))
        high = p + Decimal(str(round(abs(step) + 0.0005, 6)))
        low = p - Decimal(str(round(abs(step) + 0.0005, 6)))
        bars.append(
            PriceBar(
                symbol="EURUSD",
                timeframe=Timeframe.D1,
                ts=start + timedelta(days=i),
                open=p,
                high=high,
                low=low,
                close=p,
                volume=Decimal("100"),
                source="test",
            )
        )
    return bars


def test_train_reports_ewma_comparison_and_forecasts() -> None:
    bars = _clustered_bars(400)
    fc = train_sklearn_vol_forecaster(bars=bars, horizon_bars=5)
    r = fc.report
    assert r.n_test > 0
    assert r.ml_mae >= 0 and r.ewma_mae >= 0
    assert set(r.feature_importances) == set(VOL_FEATURE_NAMES)
    assert isinstance(r.beats_ewma, bool)
    assert "EWMA" in r.verdict

    vf = fc.forecast_vol(
        bars=bars,
        symbol="EURUSD",
        timeframe=Timeframe.D1,
        horizon_bars=5,
        pip_size=Decimal("0.0001"),
    )
    assert vf.expected_vol >= 0
    assert vf.expected_range_pips >= 0
    assert vf.model_name.startswith("sklearn_vol_hgb")


def test_train_rejects_too_few_bars() -> None:
    with pytest.raises(ValidationError):
        train_sklearn_vol_forecaster(bars=_clustered_bars(100), horizon_bars=5)


def test_macro_augmented_vol_model_carries_macro_features() -> None:
    bars = _clustered_bars(400)
    # A trivial constant macro series aligned to every bar.
    macro_by_ts = {b.ts: {name: 0.5 for name in MACRO_FEATURE_NAMES} for b in bars}
    fc = train_sklearn_vol_forecaster(bars=bars, horizon_bars=10, macro_by_ts=macro_by_ts)
    assert fc.uses_macro
    assert set(fc.macro_feature_names) == set(MACRO_FEATURE_NAMES)
    assert set(fc.report.feature_importances) >= set(MACRO_FEATURE_NAMES)
    assert fc.name.endswith(",macro)")

    # Forecasting with macro supplied must still produce a valid read.
    vf = fc.forecast_vol(
        bars=bars,
        symbol="EURUSD",
        timeframe=Timeframe.D1,
        horizon_bars=10,
        pip_size=Decimal("0.0001"),
        macro={name: 0.5 for name in MACRO_FEATURE_NAMES},
    )
    assert vf.expected_vol >= 0
