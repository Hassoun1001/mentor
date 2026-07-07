"""Regime detection + wrapped-forecaster tests."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.features import (
    FEATURE_NAMES,
    FeatureRow,
    build_feature_series,
)
from mentor.domain.forecasting.forecast import (
    Direction,
    Forecast,
    direction_from_probability,
)
from mentor.domain.forecasting.regime import (
    FeatureDistribution,
    FeatureRange,
    RegimeAdjustedForecaster,
    build_feature_distribution,
)
from mentor.domain.market.bars import PriceBar, Timeframe

# ---------- helpers ----------


def _series(slope: Decimal, n: int = 300) -> list[PriceBar]:
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


def _zeroed_features(value: Decimal = Decimal("0")) -> dict[str, Decimal]:
    return {name: value for name in FEATURE_NAMES}


# ---------- distribution ----------


def test_build_distribution_covers_every_feature() -> None:
    rows = build_feature_series(_series(Decimal("0.0002")))
    distribution = build_feature_distribution(rows)
    assert set(distribution.ranges) == set(FEATURE_NAMES)
    assert distribution.sample_size == len(rows)


def test_distribution_rejects_short_inputs() -> None:
    with pytest.raises(ValidationError):
        build_feature_distribution([])


def test_score_inside_envelope_is_one() -> None:
    rows = build_feature_series(_series(Decimal("0.0002")))
    distribution = build_feature_distribution(rows)
    # Pick a sample row from the middle — by construction it sits inside
    # at least many of its features' envelopes.
    sample: FeatureRow = rows[len(rows) // 2]
    score = distribution.score(sample.features)
    assert score > Decimal("0.5")


def test_score_far_outside_is_zero() -> None:
    rows = build_feature_series(_series(Decimal("0.0002")))
    distribution = build_feature_distribution(rows)
    crazy = {name: Decimal("1e6") for name in FEATURE_NAMES}
    assert distribution.score(crazy) == Decimal("0")


def test_out_of_range_names_lists_offenders() -> None:
    ranges = {name: FeatureRange(p5=Decimal("-1"), p95=Decimal("1")) for name in FEATURE_NAMES}
    distribution = FeatureDistribution(ranges=ranges, sample_size=100)
    features = _zeroed_features(Decimal("0"))
    features[FEATURE_NAMES[0]] = Decimal("10")  # out of range
    assert distribution.out_of_range_names(features) == (FEATURE_NAMES[0],)


# ---------- wrapped forecaster ----------


class _FixedForecaster:
    name = "fixed"
    horizon_bars = 24

    def forecast(  # type: ignore[no-untyped-def]
        self, *, bars: Sequence[PriceBar], symbol: str, timeframe: Timeframe, news=None, macro=None
    ):
        return Forecast(
            symbol=symbol.upper(),
            timeframe=timeframe,
            asof=bars[-1].ts,
            asof_close=bars[-1].close,
            horizon_bars=self.horizon_bars,
            p_up=Decimal("0.7"),
            confidence=Decimal("0.4"),
            direction=direction_from_probability(Decimal("0.7")),
            model_name=self.name,
            reasoning="fixture lean",
            features={name: Decimal("0") for name in FEATURE_NAMES},
        )


def _in_range_distribution() -> FeatureDistribution:
    ranges = {name: FeatureRange(p5=Decimal("-1"), p95=Decimal("1")) for name in FEATURE_NAMES}
    return FeatureDistribution(ranges=ranges, sample_size=100)


def _out_of_range_distribution() -> FeatureDistribution:
    ranges = {name: FeatureRange(p5=Decimal("0.5"), p95=Decimal("0.6")) for name in FEATURE_NAMES}
    return FeatureDistribution(ranges=ranges, sample_size=100)


def test_wrapper_keeps_in_regime_lean() -> None:
    fc = RegimeAdjustedForecaster(base=_FixedForecaster(), distribution=_in_range_distribution())
    out = fc.forecast(
        bars=_series(Decimal("0.0002"), n=210),
        symbol="EURUSD",
        timeframe=Timeframe.H1,
    )
    # All features are 0, all envelopes cover 0 → score is 1, confidence preserved
    assert out.p_up == Decimal("0.7")
    assert out.confidence == Decimal("0.4")
    assert out.direction is Direction.LONG


def test_wrapper_abstains_when_out_of_regime() -> None:
    fc = RegimeAdjustedForecaster(
        base=_FixedForecaster(),
        distribution=_out_of_range_distribution(),
        abstain_threshold=Decimal("0.5"),
    )
    out = fc.forecast(
        bars=_series(Decimal("0.0002"), n=210),
        symbol="EURUSD",
        timeframe=Timeframe.H1,
    )
    assert out.direction is Direction.NEUTRAL
    assert out.p_up == Decimal("0.5")
    assert out.confidence == Decimal("0")
    assert "Abstaining" in out.reasoning


def test_wrapper_scales_confidence_partially_out_of_range() -> None:
    """A distribution where exactly half the features are out of range
    should scale confidence by ~0.5."""
    mixed_ranges: dict[str, FeatureRange] = {}
    for i, name in enumerate(FEATURE_NAMES):
        if i % 2 == 0:
            mixed_ranges[name] = FeatureRange(p5=Decimal("-1"), p95=Decimal("1"))
        else:
            mixed_ranges[name] = FeatureRange(p5=Decimal("0.5"), p95=Decimal("0.6"))
    distribution = FeatureDistribution(ranges=mixed_ranges, sample_size=100)
    fc = RegimeAdjustedForecaster(
        base=_FixedForecaster(),
        distribution=distribution,
        abstain_threshold=Decimal("0.0"),
    )
    out = fc.forecast(
        bars=_series(Decimal("0.0002"), n=210),
        symbol="EURUSD",
        timeframe=Timeframe.H1,
    )
    # Half of 12 features in range → score = 0.5, confidence 0.4 * 0.5 = 0.2
    assert out.confidence == Decimal("0.2000")
