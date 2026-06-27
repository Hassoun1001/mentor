"""Regime detection.

> Flags when current conditions are unlike the training data and lowers
> confidence or abstains.   — Mentor plan, §6.D

This is Principle 05 ("Honesty about uncertainty") made concrete. A model
trained on calm markets is, by construction, ignorant of crashes. The
honest thing isn't to give the calm-market answer with full confidence
— it's to flag the user and back off.

The implementation is deliberately simple and auditable:

- During training, record the **5th and 95th percentile** of every
  feature on the training set. That's the empirical "normal range."
- At inference, count how many of the current features fall inside
  their per-feature normal range. The fraction is the regime score
  in `[0, 1]`.
- Wrap any `Forecaster` with `RegimeAdjustedForecaster`: the wrapped
  forecaster's `confidence` is multiplied by the regime score, and
  if the score is below `abstain_threshold` the wrapper returns a
  neutral, low-confidence "abstain" forecast.

We do not use Mahalanobis distance or KDEs: a Decimal-clean per-feature
quantile check is faster, has no math-library dependency in the domain
layer, and is the kind of thing a trader can verify by hand.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.features import (
    FEATURE_NAMES,
    FeatureRow,
    build_feature_row,
)
from mentor.domain.forecasting.forecast import (
    Direction,
    Forecast,
    direction_from_probability,
)
from mentor.domain.forecasting.forecaster import Forecaster
from mentor.domain.market.bars import PriceBar, Timeframe


@dataclass(frozen=True, slots=True)
class FeatureRange:
    """Empirical [p5, p95] range for a single feature."""

    p5: Decimal
    p95: Decimal

    def __post_init__(self) -> None:
        if self.p95 < self.p5:
            raise ValidationError("p95 must be >= p5", field="p95")

    def contains(self, value: Decimal) -> bool:
        return self.p5 <= value <= self.p95


@dataclass(frozen=True, slots=True)
class FeatureDistribution:
    """Empirical envelope across all engineered features.

    Built from training rows so the regime check is grounded in the data
    the model actually saw — not a hand-tuned threshold.
    """

    ranges: Mapping[str, FeatureRange]
    sample_size: int

    def __post_init__(self) -> None:
        if self.sample_size <= 0:
            raise ValidationError("sample_size must be positive")
        missing = set(FEATURE_NAMES) - set(self.ranges)
        if missing:
            raise ValidationError(f"feature distribution missing ranges for {sorted(missing)}")

    def score(self, features: Mapping[str, Decimal]) -> Decimal:
        """Fraction of features inside their normal range, in [0, 1]."""
        in_range = sum(
            1
            for name in FEATURE_NAMES
            if name in features and self.ranges[name].contains(features[name])
        )
        return Decimal(in_range) / Decimal(len(FEATURE_NAMES))

    def out_of_range_names(self, features: Mapping[str, Decimal]) -> tuple[str, ...]:
        return tuple(
            name
            for name in FEATURE_NAMES
            if name in features and not self.ranges[name].contains(features[name])
        )


def _quantile(sorted_values: Sequence[Decimal], q: float) -> Decimal:
    if not sorted_values:
        raise ValidationError("cannot compute quantile on empty sequence")
    idx = max(0, min(len(sorted_values) - 1, int(q * (len(sorted_values) - 1))))
    return sorted_values[idx]


def build_feature_distribution(
    rows: Sequence[FeatureRow],
    *,
    lo_q: float = 0.05,
    hi_q: float = 0.95,
) -> FeatureDistribution:
    if len(rows) < 20:
        raise ValidationError("need at least 20 feature rows to estimate the distribution")
    ranges: dict[str, FeatureRange] = {}
    for name in FEATURE_NAMES:
        values = sorted(row.features[name] for row in rows if name in row.features)
        if not values:
            raise ValidationError(f"no values for feature {name!r}")
        ranges[name] = FeatureRange(p5=_quantile(values, lo_q), p95=_quantile(values, hi_q))
    return FeatureDistribution(ranges=ranges, sample_size=len(rows))


# ---------------------------------------------------------------------------
# Wrapped forecaster
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class RegimeAdjustedForecaster(Forecaster):
    """Wraps a base forecaster with a regime check.

    The base forecaster runs unchanged. We then:

    1. Compute the regime score from the same feature row used by the
       forecast (re-derived from `bars`).
    2. If the score is below `abstain_threshold`, return a neutral
       abstain forecast — the user sees this in plain language rather
       than a quietly downweighted but still-confident-looking call.
    3. Otherwise, multiply the base confidence by the score so the
       displayed confidence reflects the regime fit.
    """

    base: Forecaster
    distribution: FeatureDistribution
    abstain_threshold: Decimal = Decimal("0.5")

    @property
    def name(self) -> str:
        return f"regime_adjusted({self.base.name})"

    @property
    def horizon_bars(self) -> int:
        return self.base.horizon_bars

    def forecast(self, *, bars: Sequence[PriceBar], symbol: str, timeframe: Timeframe) -> Forecast:
        row = build_feature_row(bars)
        base = self.base.forecast(bars=bars, symbol=symbol, timeframe=timeframe)

        if row is None:
            return base  # nothing to check against; defer

        regime_score = self.distribution.score(row.features)
        out_of_range = self.distribution.out_of_range_names(row.features)

        if regime_score < self.abstain_threshold:
            preview = ", ".join(out_of_range[:3])
            reasoning = (
                f"Abstaining: only {regime_score * 100:.0f}% of features sit inside the "
                f"5-95th percentile envelope the model was trained on "
                f"({len(out_of_range)} of {len(row.features)} features are off-distribution"
                f"{f' — {preview}' if preview else ''}). The model has no business making "
                f"a call here. Trade discretionary or wait for the regime to normalise."
            )
            return Forecast(
                symbol=base.symbol,
                timeframe=base.timeframe,
                asof=base.asof,
                asof_close=base.asof_close,
                horizon_bars=base.horizon_bars,
                p_up=Decimal("0.5"),
                confidence=Decimal("0"),
                direction=Direction.NEUTRAL,
                model_name=self.name,
                reasoning=reasoning,
                features=base.features,
            )

        adjusted_conf = (base.confidence * regime_score).quantize(Decimal("0.0001"))
        notes = base.reasoning
        if out_of_range:
            preview = ", ".join(out_of_range[:3])
            notes = (
                f"{notes} Regime fit {regime_score * 100:.0f}% — "
                f"{len(out_of_range)} feature(s) outside the training envelope ({preview}); "
                f"confidence shrunk to match."
            )
        # Re-derive direction with the new confidence so the neutral band is honoured.
        direction = direction_from_probability(base.p_up)
        return Forecast(
            symbol=base.symbol,
            timeframe=base.timeframe,
            asof=base.asof,
            asof_close=base.asof_close,
            horizon_bars=base.horizon_bars,
            p_up=base.p_up,
            confidence=adjusted_conf,
            direction=direction,
            model_name=self.name,
            reasoning=notes,
            features=base.features,
        )
