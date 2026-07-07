"""Stock quote client — daily closes for any ticker (Yahoo, free, no key).

Separate from the FX `MarketDataAdapter` on purpose: tip scoring only
needs a daily close series per US ticker (entry price at the mention
date, the latest price, and the high/low since), not full OHLCV bars on a
Timeframe grid. Keeping it small keeps the tips feature independent of the
forecasting pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from mentor.domain.errors import DomainError

_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class StockQuoteError(DomainError):
    """Quote provider failed or has no data for the ticker."""


@dataclass(frozen=True, slots=True)
class DailyClose:
    day: datetime
    close: Decimal


class StockQuoteClient:
    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        self._owns = client is None
        self._client = client or httpx.AsyncClient(timeout=20.0, headers={"User-Agent": _UA})

    async def aclose(self) -> None:
        if self._owns:
            await self._client.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        wait=wait_exponential_jitter(initial=0.5, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def daily_closes(
        self, *, ticker: str, start: datetime, end: datetime
    ) -> list[DailyClose]:
        params = {
            "period1": str(int(start.astimezone(UTC).timestamp())),
            "period2": str(int(end.astimezone(UTC).timestamp())),
            "interval": "1d",
        }
        resp = await self._client.get(f"{_BASE}/{ticker.upper()}", params=params)
        resp.raise_for_status()
        payload = resp.json()
        chart = payload.get("chart") or {}
        if chart.get("error"):
            raise StockQuoteError(f"{ticker}: {chart['error']}")
        results = chart.get("result") or []
        if not results:
            return []
        result = results[0]
        stamps = result.get("timestamp") or []
        quote = (result.get("indicators", {}).get("quote") or [{}])[0]
        closes = quote.get("close") or []
        out: list[DailyClose] = []
        for i, ts in enumerate(stamps):
            c = closes[i] if i < len(closes) else None
            if c is None:
                continue
            out.append(DailyClose(day=datetime.fromtimestamp(ts, UTC), close=Decimal(str(c))))
        return out
