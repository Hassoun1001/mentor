"""Volatility feature engineering — presence + point-in-time safety."""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.domain.forecasting.vol_features import (
    VOL_FEATURE_NAMES,
    build_vol_feature_row,
    build_vol_feature_series,
)
from mentor.domain.market.bars import PriceBar, Timeframe


def _bars(prices: list[Decimal]) -> list[PriceBar]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        PriceBar(
            symbol="EURUSD",
            timeframe=Timeframe.D1,
            ts=start + timedelta(days=i),
            open=p,
            high=p + Decimal("0.0010"),
            low=p - Decimal("0.0010"),
            close=p,
            volume=Decimal("100"),
            source="test",
        )
        for i, p in enumerate(prices)
    ]


def _wiggly(n: int) -> list[Decimal]:
    return [Decimal("1.10") + Decimal(str((i % 7) * 0.0013)) for i in range(n)]


def test_short_series_returns_none() -> None:
    assert build_vol_feature_row(_bars([Decimal("1.10")] * 10)) is None


def test_full_vol_row_has_all_named_features() -> None:
    row = build_vol_feature_row(_bars(_wiggly(80)))
    assert row is not None
    assert set(row.features) == set(VOL_FEATURE_NAMES)
    for name in VOL_FEATURE_NAMES:
        assert isinstance(row.features[name], Decimal)


def test_vol_series_timestamps_increasing() -> None:
    series = build_vol_feature_series(_bars(_wiggly(120)))
    assert len(series) > 1
    for a, b in itertools.pairwise(series):
        assert a.ts < b.ts


def test_vol_features_are_point_in_time() -> None:
    bars = _bars(_wiggly(120))
    series = build_vol_feature_series(bars)
    assert series
    sample = series[-1]
    idx = next(i for i, b in enumerate(bars) if b.ts == sample.ts)
    rebuilt = build_vol_feature_row(bars[: idx + 1])
    assert rebuilt is not None
    for name in VOL_FEATURE_NAMES:
        assert rebuilt.features[name] == sample.features[name]
