"""Price-bar query endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from mentor.api.deps import SessionDep, SettingsDep
from mentor.application.market import IngestionService, scan_quality
from mentor.application.market.cross_source import compare_sources
from mentor.domain.errors import DomainError
from mentor.domain.market.adapter import MarketDataAdapter
from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.adapters import FailoverMarketDataAdapter
from mentor.infrastructure.adapters.factory import build_adapter, build_sources, close_sources
from mentor.infrastructure.repositories.price_bars import PriceBarRepository

router = APIRouter(prefix="/prices", tags=["market"])

# Default chart lookback per timeframe (from the newest bar available).
_DEFAULT_WINDOW_DAYS: dict[Timeframe, int] = {
    Timeframe.M1: 5,
    Timeframe.M5: 21,
    Timeframe.H1: 120,
    Timeframe.D1: 400,
}

SourceName = Literal["failover", "twelve_data", "yahoo"]


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
    # Bars the market has not finished printing. Their OHLC is still moving,
    # so a model trained on settled bars is serving from an unsettled one.
    forming_bars: int = 0
    future_bars: int = 0


class CoverageRowDTO(BaseModel):
    timeframe: str
    bars: int
    first_ts: datetime | None
    last_ts: datetime | None
    sources: dict[str, int]
    # A bar stamped after 'now' cannot be right under any labelling
    # convention. Production carried a daily bar dated tomorrow — Yahoo
    # names the in-progress FX session by its close date — and the health
    # page had no way to show it.
    future_bars: int = 0
    newest_is_forming: bool = False


class CoverageResponse(BaseModel):
    symbol: str
    coverage: list[CoverageRowDTO]


@router.get("/{symbol}/coverage", response_model=CoverageResponse)
async def coverage(symbol: str, session: SessionDep) -> CoverageResponse:
    """How much price data exists, over what span, and from which sources."""
    rows = await PriceBarRepository(session).coverage(symbol=symbol)
    now = datetime.now(UTC)
    return CoverageResponse(
        symbol=symbol.upper(),
        coverage=[
            CoverageRowDTO(
                timeframe=r.timeframe,
                bars=r.bars,
                first_ts=r.first_ts,
                last_ts=r.last_ts,
                sources=r.sources,
                future_bars=1 if (r.last_ts is not None and r.last_ts > now) else 0,
                newest_is_forming=(
                    r.last_ts is not None
                    and r.last_ts <= now
                    and r.last_ts.timestamp() + Timeframe(r.timeframe).seconds
                    > now.timestamp()
                ),
            )
            for r in rows
        ],
    )


class IngestPricesRequest(BaseModel):
    timeframe: Timeframe = Timeframe.D1
    days_back: Annotated[int, Field(ge=1, le=4000)] = 3650
    source: SourceName = "failover"


class IngestPricesResponse(BaseModel):
    symbol: str
    timeframe: Timeframe
    source: str
    fetched: int
    persisted: int


@router.post("/{symbol}/ingest", response_model=IngestPricesResponse)
async def ingest_prices(
    symbol: str, body: IngestPricesRequest, session: SessionDep, settings: SettingsDep
) -> IngestPricesResponse:
    """Backfill bars from a chosen source (or failover). Yahoo (no key)
    reaches ~10y of daily history for deep backfills."""
    adapter: MarketDataAdapter
    if body.source == "failover":
        sources = build_sources(settings)
        adapter = FailoverMarketDataAdapter(sources)
        to_close = sources
    else:
        one = build_adapter(body.source, settings)
        if one is None:
            raise HTTPException(
                status_code=400,
                detail=f"source '{body.source}' is not configured (needs an API key).",
            )
        adapter = one
        to_close = [one]

    end = datetime.now(UTC)
    start = end - timedelta(days=body.days_back)
    try:
        service = IngestionService(adapter=adapter, repo=PriceBarRepository(session))
        result = await service.ingest(
            symbol=symbol.upper(), timeframe=body.timeframe, start=start, end=end
        )
    except DomainError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        await close_sources(to_close)
    return IngestPricesResponse(
        symbol=result.symbol,
        timeframe=result.timeframe,
        source=getattr(adapter, "last_source", None) or adapter.name,
        fetched=result.fetched,
        persisted=result.persisted,
    )


class CrossSourceResponse(BaseModel):
    symbol: str
    timeframe: Timeframe
    source_a: str
    source_b: str
    bars_a: int
    bars_b: int
    overlapping: int
    max_abs_diff: Decimal
    mean_abs_diff: Decimal
    max_diff_pips: float
    mean_diff_pips: float
    agree: bool


@router.get("/{symbol}/cross-source", response_model=CrossSourceResponse)
async def cross_source(
    symbol: str,
    settings: SettingsDep,
    timeframe: Timeframe = Timeframe.D1,
    days_back: int = Query(default=45, ge=2, le=365),
) -> CrossSourceResponse:
    """Compare Twelve Data vs Yahoo closes over a recent window — flags when
    the two feeds disagree (stale, mis-scaled, or different fixing time)."""
    primary = build_adapter("twelve_data", settings)
    secondary = build_adapter("yahoo", settings)
    if primary is None or secondary is None:
        raise HTTPException(
            status_code=400,
            detail="cross-source needs both Twelve Data (key) and Yahoo configured.",
        )
    end = datetime.now(UTC)
    start = end - timedelta(days=days_back)
    try:
        report = await compare_sources(
            primary=primary,
            secondary=secondary,
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
        )
    finally:
        await close_sources([primary, secondary])
    return CrossSourceResponse(
        symbol=report.symbol,
        timeframe=report.timeframe,
        source_a=report.source_a,
        source_b=report.source_b,
        bars_a=report.bars_a,
        bars_b=report.bars_b,
        overlapping=report.overlapping,
        max_abs_diff=report.max_abs_diff,
        mean_abs_diff=report.mean_abs_diff,
        max_diff_pips=float(report.max_abs_diff) * 10000,
        mean_diff_pips=float(report.mean_abs_diff) * 10000,
        agree=report.agree,
    )


@router.get("/{symbol}", response_model=PricesResponse)
async def get_prices(
    symbol: str,
    session: SessionDep,
    timeframe: Timeframe = Timeframe.H1,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
) -> PricesResponse:
    repo = PriceBarRepository(session)
    # Anchor the default window to the newest bar we actually have, not to
    # "now" — otherwise a stale local dataset (no ingest for a week) falls
    # outside a now-relative window and the chart shows nothing.
    if end is None:
        latest = await repo.latest(symbol=symbol, timeframe=timeframe)
        end = (latest.ts + timedelta(seconds=1)) if latest is not None else datetime.now(UTC)
    if start is None:
        start = end - timedelta(days=_DEFAULT_WINDOW_DAYS.get(timeframe, 120))

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
        forming_bars=report.forming_bars,
        future_bars=report.future_bars,
    )
