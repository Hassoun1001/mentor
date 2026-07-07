"""Macro context loading — bridges the macro repo to model features.

Loads the persisted FRED series into the pure ``MacroSeries`` and produces
the point-in-time macro-feature maps the trainer and forecaster consume.
All point-in-time safety lives in ``MacroSeries.features_asof`` — this
module only moves data. Mirrors ``news_context``.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from mentor.domain.forecasting.macro_features import MacroPoint, MacroSeries
from mentor.infrastructure.repositories.macro_series import MacroSeriesRepository


async def load_macro_series(repo: MacroSeriesRepository) -> MacroSeries:
    rows = await repo.series()
    points = [
        MacroPoint(series_id=r.series_id, day=r.day, value=float(r.value)) for r in rows
    ]
    return MacroSeries(points)


def build_macro_by_ts(
    series: MacroSeries, timestamps: Sequence[datetime]
) -> dict[datetime, dict[str, float]]:
    """Per-bar macro features keyed by bar timestamp (training alignment)."""
    return {ts: series.features_asof(ts) for ts in timestamps}
