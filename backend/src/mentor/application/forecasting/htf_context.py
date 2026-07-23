"""Higher-timeframe context loading — the daily picture for an intraday model.

Mirrors the news/macro context helpers: load the higher-timeframe bars
once, wrap them in an ``HtfSeries``, and align them point-in-time to the
lower-timeframe bar timestamps. All the lookahead safety lives in
``HtfSeries`` (only *closed* higher-timeframe bars are ever visible).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from mentor.domain.forecasting.htf_features import HtfSeries
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.repositories.price_bars import PriceBarRepository

# The higher timeframe an intraday lane looks up to. Daily is the natural
# "bigger picture" for an hourly model and is already ingested.
HTF_TIMEFRAME = Timeframe.D1


def _to_domain(rows) -> list[PriceBar]:  # type: ignore[no-untyped-def]
    return [
        PriceBar(
            symbol=r.symbol,
            timeframe=Timeframe(r.timeframe),
            ts=r.ts,
            open=Decimal(r.open),
            high=Decimal(r.high),
            low=Decimal(r.low),
            close=Decimal(r.close),
            volume=Decimal(r.volume) if r.volume is not None else None,
            source=r.source,
        )
        for r in rows
    ]


async def load_htf_series(
    repo: PriceBarRepository,
    *,
    symbol: str,
    timeframe: Timeframe = HTF_TIMEFRAME,
) -> HtfSeries:
    """All stored higher-timeframe bars for the symbol, ready for lookup."""
    rows = await repo.range(
        symbol=symbol,
        timeframe=timeframe,
        start=datetime(2000, 1, 1, tzinfo=UTC),
        end=datetime(2100, 1, 1, tzinfo=UTC),
    )
    return HtfSeries(_to_domain(rows))


def build_htf_by_ts(
    series: HtfSeries, timestamps: Sequence[datetime]
) -> dict[datetime, dict[str, float]]:
    return {ts: series.features_asof(ts) for ts in timestamps}
