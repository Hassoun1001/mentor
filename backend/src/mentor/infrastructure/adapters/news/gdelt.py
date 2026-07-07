"""GDELT adapter — free historical news sentiment.

GDELT's DOC 2.0 API exposes daily timelines for any boolean query, with
no API key. We pull two series for a macro query (ECB / Fed / euro-dollar):

- **Average Tone** — mean sentiment of matching coverage that day,
  roughly -10..+10 (negative = more negative coverage). This is the
  signed signal the forecaster can actually lean on.
- **Volume Intensity** — share of global coverage matching the query,
  a proxy for how *loud* the news flow was that day.

GDELT asks for ≤ 1 request / 5s, so the adapter throttles between calls.
History reaches back years at daily resolution — which is exactly what we
need to align news to the daily price bars without lookahead.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from mentor.domain.errors import DomainError
from mentor.logging import get_logger

log = get_logger("mentor.adapters.gdelt")

_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
_MIN_INTERVAL_S = 5.5  # GDELT: one request / 5s; add headroom


class GdeltError(DomainError):
    """GDELT request failed or returned an unusable response."""


@dataclass(frozen=True, slots=True)
class DailyTone:
    day: datetime  # midnight UTC
    tone: float
    volume: float


def _parse_timeline(payload: dict[str, Any]) -> dict[datetime, float]:
    out: dict[datetime, float] = {}
    for series in payload.get("timeline", []):
        for point in series.get("data", []):
            raw = point.get("date", "")
            try:
                day = datetime.strptime(raw[:8], "%Y%m%d").replace(tzinfo=UTC)
            except (ValueError, TypeError):
                continue
            out[day] = float(point.get("value", 0.0))
    return out


class GdeltNewsAdapter:
    """Fetches daily tone + volume for a macro query over a date range."""

    def __init__(self, *, query: str, client: httpx.AsyncClient | None = None) -> None:
        self._query = query
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> GdeltNewsAdapter:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30, headers={"User-Agent": "mentor/1.0 (+local research)"}
            )
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()

    async def _timeline(
        self, mode: str, start: datetime, end: datetime, *, max_retries: int = 6
    ) -> dict[datetime, float]:
        assert self._client is not None
        params = {
            "query": self._query,
            "mode": mode,
            "format": "json",
            "startdatetime": start.strftime("%Y%m%d000000"),
            "enddatetime": end.strftime("%Y%m%d235959"),
        }
        last_err = "unknown"
        for attempt in range(max_retries):
            try:
                resp = await self._client.get(_BASE, params=params)
            except httpx.HTTPError as exc:  # network failure
                raise GdeltError(f"GDELT request failed: {exc}") from exc
            text = resp.text.strip()
            # 429 *and* the plain-text throttle message both mean "slow down".
            throttled = resp.status_code == 429 or text.startswith("Please limit requests")
            if throttled:
                last_err = "rate limited"
                await asyncio.sleep(_MIN_INTERVAL_S * (attempt + 2))  # 11s, 16.5s, 22s…
                continue
            if resp.status_code != 200:
                raise GdeltError(f"GDELT returned {resp.status_code}")
            if not text.startswith("{"):
                raise GdeltError(f"GDELT non-JSON response: {text[:120]}")
            return _parse_timeline(resp.json())
        raise GdeltError(f"GDELT {last_err} after {max_retries} attempts")

    async def fetch_range(self, *, start: datetime, end: datetime) -> list[DailyTone]:
        """Return one DailyTone per day GDELT reports in [start, end].

        GDELT caps a single query's span, so we fetch in ≤ 365-day windows
        and throttle between every HTTP call.
        """
        tone: dict[datetime, float] = {}
        volume: dict[datetime, float] = {}

        # GDELT timeline modes accept multi-year spans, so one window is
        # usually enough — fewer HTTP calls means less rate-limit exposure.
        windows = _split_windows(start, end, max_days=3650)
        first = True
        for w_start, w_end in windows:
            if not first:
                await asyncio.sleep(_MIN_INTERVAL_S)
            tone.update(await self._timeline("timelinetone", w_start, w_end))
            await asyncio.sleep(_MIN_INTERVAL_S)
            # Volume is a secondary feature; if GDELT throttles it we still
            # ship the (signed) tone rather than failing the whole backfill.
            try:
                volume.update(await self._timeline("timelinevol", w_start, w_end))
            except GdeltError as exc:
                log.warning("gdelt.volume_skipped", error=str(exc))
            first = False
            log.info("gdelt.window", start=w_start.date().isoformat(), end=w_end.date().isoformat())

        days = sorted(set(tone) | set(volume))
        return [
            DailyTone(day=d, tone=tone.get(d, 0.0), volume=volume.get(d, 0.0)) for d in days
        ]


def _split_windows(
    start: datetime, end: datetime, *, max_days: int
) -> list[tuple[datetime, datetime]]:
    out: list[tuple[datetime, datetime]] = []
    cursor = start
    step = timedelta(days=max_days)
    while cursor < end:
        w_end = min(cursor + step, end)
        out.append((cursor, w_end))
        cursor = w_end
    return out or [(start, end)]
