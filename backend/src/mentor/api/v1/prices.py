"""Price-bar query endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from mentor.api.deps import SessionDep
from mentor.application.market import scan_quality
from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.repositories.price_bars import PriceBarRepository

router = APIRouter(prefix="/prices", tags=["market"])


class BarDTO(BaseModel):
    ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None
    source: str


class GapDTO(BaseModel):
    expected_after: datetime
    next_seen: datetime
    missing_bars: int


class PricesResponse(BaseModel):
    symbol: str
    timeframe: Timeframe
    bars: list[BarDTO]
    gaps: list[GapDTO]
    last_seen_at: datetime | None


@router.get("/{symbol}", response_model=PricesResponse)
async def get_prices(
    symbol: str,
    session: SessionDep,
    timeframe: Timeframe = Timeframe.H1,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
) -> PricesResponse:
    repo = PriceBarRepository(session)
    end = end or datetime.now(UTC)
    start = start or (end - timedelta(days=7))

    bars = await repo.range(symbol=symbol, timeframe=timeframe, start=start, end=end)
    report = scan_quality(symbol=symbol.upper(), timeframe=timeframe, bars=bars)

    return PricesResponse(
        symbol=symbol.upper(),
        timeframe=timeframe,
        bars=[
            BarDTO(
                ts=b.ts,
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
                source=b.source,
            )
            for b in bars
        ],
        gaps=[
            GapDTO(
                expected_after=g.expected_after,
                next_seen=g.next_seen,
                missing_bars=g.missing_bars,
            )
            for g in report.gaps
        ],
        last_seen_at=report.last_seen_at,
    )
