"""News context loading — bridges the tone repository to model features.

Loads the persisted GDELT tone series into the pure domain
``NewsToneSeries`` and produces the point-in-time news-feature maps the
trainer and the forecaster consume. All point-in-time safety lives in
``NewsToneSeries.features_asof`` — this module only moves data.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from mentor.domain.forecasting.news_features import NewsTonePoint, NewsToneSeries
from mentor.infrastructure.repositories.news_tone import NewsToneRepository


async def load_news_series(repo: NewsToneRepository, *, query_key: str) -> NewsToneSeries:
    rows = await repo.series(query_key=query_key)
    points = [
        NewsTonePoint(day=r.day, tone=float(r.tone), volume=float(r.volume)) for r in rows
    ]
    return NewsToneSeries(points)


def build_news_by_ts(
    series: NewsToneSeries, timestamps: Sequence[datetime]
) -> dict[datetime, dict[str, float]]:
    """Per-bar news features keyed by bar timestamp (training alignment)."""
    return {ts: series.features_asof(ts) for ts in timestamps}
