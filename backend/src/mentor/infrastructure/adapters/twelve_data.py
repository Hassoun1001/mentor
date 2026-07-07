"""Twelve Data — first concrete market-data adapter.

API docs: https://twelvedata.com/docs

Design choices that matter:
- httpx.AsyncClient is passed in (not created) so callers control its
  lifetime — usually one client per process for connection pooling.
- tenacity drives retries with exponential backoff; only transient HTTP
  errors retry, not 4xx (those are user errors and won't fix themselves).
- The API key is read from `Settings` and never logged.
- Timestamps from the provider are interpreted as UTC unless tagged
  otherwise. Twelve Data returns naive ISO strings — we attach UTC.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
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
    Timeframe.M1: "1min",
    Timeframe.M5: "5min",
    Timeframe.H1: "1h",
    Timeframe.D1: "1day",
}


class TwelveDataError(DomainError):
    """Provider returned a structured error (auth, rate limit, bad symbol…)."""


class TwelveDataAdapter(MarketDataAdapter):
    name = "twelve_data"
    _BASE_URL: Final = "https://api.twelvedata.com"

    def __init__(self, *, api_key: str, client: httpx.AsyncClient | None = None) -> None:
        if not api_key:
            raise ValueError("TwelveDataAdapter requires an api_key")
        self._api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        wait=wait_exponential_jitter(initial=0.5, max=8),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    async def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        response = await self._client.get(
            f"{self._BASE_URL}{path}",
            params={**params, "apikey": self._api_key, "format": "JSON"},
        )
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        # Twelve Data uses HTTP 200 for application errors with `status=error`.
        if body.get("status") == "error":
            raise TwelveDataError(body.get("message", "Twelve Data error"))
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
            "symbol": _format_symbol(symbol),
            "interval": interval,
            "start_date": start.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": end.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": "UTC",
            "order": "ASC",
            "outputsize": "5000",
        }
        body = await self._get("/time_series", params)
        values = body.get("values") or []
        for row in values:
            yield PriceBar(
                symbol=symbol,
                timeframe=timeframe,
                ts=_parse_ts(row["datetime"]),
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=Decimal(str(row["volume"])) if row.get("volume") else None,
                source=self.name,
            )


def _format_symbol(symbol: str) -> str:
    """Twelve Data wants e.g. `EUR/USD`, not `EURUSD`."""
    s = symbol.upper().replace("/", "")
    if len(s) == 6:
        return f"{s[:3]}/{s[3:]}"
    return symbol


def _parse_ts(value: str) -> datetime:
    # Twelve Data timestamps are already UTC (we pass timezone=UTC). Intraday
    # bars carry a time ("2026-06-25 14:30:00"); daily/weekly bars are
    # date-only ("2026-06-25"). Handle both, plus the ISO "T" separator.
    text = value.strip()
    if "T" in text:
        return datetime.fromisoformat(text).replace(tzinfo=UTC)
    fmt = "%Y-%m-%d %H:%M:%S" if " " in text else "%Y-%m-%d"
    return datetime.strptime(text, fmt).replace(tzinfo=UTC)
