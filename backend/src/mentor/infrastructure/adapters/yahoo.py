"""Yahoo Finance — second market-data source (free, no key).

Yahoo's public chart endpoint returns OHLC with deep history (10y+ daily)
and no API key, which makes it both a **redundant** source for failover
and a way to backfill far more history than the Twelve Data free tier
allows. It's an unofficial endpoint, so we treat it defensively: a
browser-like User-Agent, tolerant null handling (Yahoo pads missing bars
with nulls), and the same retry policy as the primary adapter.

Intraday intervals have range ceilings on Yahoo's side (≈730d for 1h,
60d for 5m, 7d for 1m); for ranges beyond those Yahoo simply returns a
shorter window, which the ingestion layer handles idempotently.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, Final

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from mentor.domain.errors import DomainError
from mentor.domain.market.adapter import MarketDataAdapter
from mentor.domain.market.bars import PriceBar, Timeframe

_TIMEFRAME_TO_INTERVAL: Final[dict[Timeframe, str]] = {
    Timeframe.M1: "1m",
    Timeframe.M5: "5m",
    Timeframe.H1: "60m",
    Timeframe.D1: "1d",
}

_BROWSER_UA: Final = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class YahooFinanceError(DomainError):
    """Yahoo returned an error payload or an unusable response."""


def _yahoo_symbol(symbol: str) -> str:
    """`EURUSD` → `EURUSD=X` (Yahoo's FX ticker convention)."""
    s = symbol.upper().replace("/", "")
    return f"{s}=X" if "=" not in symbol else symbol


def _normalise_ts(ts: int, timeframe: Timeframe) -> datetime:
    """Align a Yahoo timestamp to the timeframe boundary the rest of the
    system uses (UTC midnight for daily).

    Yahoo dates a *daily* bar at the exchange-local midnight — for the
    Europe/London FX session that's 23:00 UTC the day before (BST) or
    00:00 UTC (GMT). Snapping to the nearest UTC midnight maps every such
    bar onto the trading day Twelve Data also uses, so the two feeds
    dedupe and align instead of doubling up. Intraday bars are already at
    real UTC interval boundaries and pass through unchanged.
    """
    dt = datetime.fromtimestamp(ts, UTC)
    if timeframe is Timeframe.D1:
        day = (dt + timedelta(hours=12)).date()  # round to nearest midnight
        return datetime(day.year, day.month, day.day, tzinfo=UTC)
    return dt


class YahooFinanceAdapter(MarketDataAdapter):
    name = "yahoo"
    _BASE_URL: Final = "https://query1.finance.yahoo.com/v8/finance/chart"

    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=20.0, headers={"User-Agent": _BROWSER_UA}
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        wait=wait_exponential_jitter(initial=0.5, max=8),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    async def _get(self, symbol: str, params: dict[str, str]) -> dict[str, Any]:
        response = await self._client.get(f"{self._BASE_URL}/{symbol}", params=params)
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        chart = body.get("chart") or {}
        if chart.get("error"):
            raise YahooFinanceError(str(chart["error"]))
        return body

    async def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> AsyncIterator[PriceBar]:
        interval = _TIMEFRAME_TO_INTERVAL[timeframe]
        params = {
            "period1": str(int(start.astimezone(UTC).timestamp())),
            "period2": str(int(end.astimezone(UTC).timestamp())),
            "interval": interval,
            "includePrePost": "false",
            "events": "div,splits",
        }
        body = await self._get(_yahoo_symbol(symbol), params)
        results = body.get("chart", {}).get("result") or []
        if not results:
            return
        result = results[0]
        timestamps = result.get("timestamp") or []
        quote_blocks = (result.get("indicators", {}).get("quote") or [{}])
        quote = quote_blocks[0] if quote_blocks else {}
        opens = quote.get("open") or []
        highs = quote.get("high") or []
        lows = quote.get("low") or []
        closes = quote.get("close") or []
        volumes = quote.get("volume") or []

        for i, ts in enumerate(timestamps):
            o, h, low_, c = (
                _at(opens, i),
                _at(highs, i),
                _at(lows, i),
                _at(closes, i),
            )
            # Yahoo pads non-trading slots with nulls — skip incomplete bars.
            if None in (o, h, low_, c):
                continue
            d_open, d_high, d_low, d_close = (
                Decimal(str(o)),
                Decimal(str(h)),
                Decimal(str(low_)),
                Decimal(str(c)),
            )
            # Yahoo's rounding can leave the reported high/low a hair inside
            # the open/close. Tighten the envelope so the bar is internally
            # consistent rather than dropping otherwise-good data.
            d_high = max(d_high, d_open, d_close)
            d_low = min(d_low, d_open, d_close)
            yield PriceBar(
                symbol=symbol.upper(),
                timeframe=timeframe,
                ts=_normalise_ts(ts, timeframe),
                open=d_open,
                high=d_high,
                low=d_low,
                close=d_close,
                volume=Decimal(str(_at(volumes, i))) if _at(volumes, i) else None,
                source=self.name,
            )


def _at(seq: list[Any], i: int) -> Any:
    return seq[i] if i < len(seq) else None
