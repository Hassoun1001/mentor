"""Forecasting domain — Phase 4.

> The language model handles language and reasoning; the quantitative
> model handles numbers. They are never swapped — an LLM has no reliable
> sense of price and must never produce a target.   — Mentor plan, §8

Every forecast is a **probability**, not a verdict, and is logged
against the eventual outcome so calibration can be measured.
"""

from mentor.domain.forecasting.features import (
    FEATURE_NAMES,
    FeatureRow,
    build_feature_row,
    build_feature_series,
)
from mentor.domain.forecasting.forecast import Direction, Forecast
from mentor.domain.forecasting.forecaster import Forecaster
from mentor.domain.forecasting.labels import build_labels
from mentor.domain.forecasting.regime import (
    FeatureDistribution,
    FeatureRange,
    RegimeAdjustedForecaster,
    build_feature_distribution,
)

__all__ = [
    "FEATURE_NAMES",
    "Direction",
    "FeatureDistribution",
    "FeatureRange",
    "FeatureRow",
    "Forecast",
    "Forecaster",
    "RegimeAdjustedForecaster",
    "build_feature_distribution",
    "build_feature_row",
    "build_feature_series",
    "build_labels",
]
