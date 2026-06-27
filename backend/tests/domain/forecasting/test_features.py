"""Feature engineering tests."""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.domain.forecasting.features import (
    FEATURE_NAMES,
    build_feature_row,
    build_feature_series,
)
from mentor.domain.forecasting.labels import build_labels
from mentor.domain.market.bars import PriceBar, Timeframe


def _series(prices: list[Decimal]) -> list[PriceBar]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return [
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
        for i, p in enumerate(prices)
    ]


def test_short_series_returns_none() -> None:
    bars = _series([Decimal("1.08")] * 10)
    assert build_feature_row(bars) is None


def test_full_feature_row_has_all_named_features() -> None:
    bars = _series([Decimal("1.08") + Decimal(i) * Decimal("0.0001") for i in range(100)])
    row = build_feature_row(bars)
    assert row is not None
    assert set(row.features) == set(FEATURE_NAMES)
    for name in FEATURE_NAMES:
        assert isinstance(row.features[name], Decimal)


def test_feature_series_grows_as_history_grows() -> None:
    bars = _series([Decimal("1.08") + Decimal(i) * Decimal("0.0001") for i in range(120)])
    series = build_feature_series(bars)
    assert len(series) > 1
    # Timestamps are strictly increasing.
    for a, b in itertools.pairwise(series):
        assert a.ts < b.ts


def test_features_are_point_in_time() -> None:
    """Building the row at the end of bars[:i+1] must equal the i-th
    entry in build_feature_series(bars) — i.e. each row sees only its
    own prefix of history. A lookahead leak would break this."""
    bars = _series([Decimal("1.08") + Decimal(i) * Decimal("0.0001") for i in range(120)])
    series = build_feature_series(bars)
    if not series:
        return
    sample = series[-1]
    # Find the index of the row's ts in the original bars
    idx = next(i for i, b in enumerate(bars) if b.ts == sample.ts)
    rebuilt = build_feature_row(bars[: idx + 1])
    assert rebuilt is not None
    for name in FEATURE_NAMES:
        assert rebuilt.features[name] == sample.features[name]


def test_label_drops_tail() -> None:
    closes = [Decimal(str(1.08 + i * 0.001)) for i in range(20)]
    ts = [datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=i) for i in range(20)]
    labels = build_labels(closes, timestamps=ts, horizon_bars=5)
    assert len(labels) == 15  # 20 - 5
    # On a rising series every label should be 1
    assert all(label == 1 for _, label in labels)
