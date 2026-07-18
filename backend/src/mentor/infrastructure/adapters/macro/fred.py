"""FRED adapter — free daily macro series, no API key.

FRED exposes any series as CSV at ``fredgraph.csv?id=<SERIES>`` with rows
``observation_date,VALUE`` and ``.`` for missing days. We pull the handful
of drivers that actually move EUR/USD (US rates, the 2s10s curve, the broad
dollar index, VIX) and cache them in ``macro_series`` so the model trains
without re-hitting the network every run — the same discipline as the GDELT
tone cache.

We probed all five series live before writing this adapter (2016–2026 daily
history, HTTP 200, clean CSV) — the throwaway-probe rule from the handover.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from mentor.domain.errors import DomainError
from mentor.logging import get_logger

log = get_logger("mentor.adapters.fred")

_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"
_MIN_INTERVAL_S = 1.0  # polite spacing between series requests
_MISSING = {".", ""}


class FredError(DomainError):
    """FRED request failed or returned an unusable response."""


@dataclass(frozen=True, slots=True)
class MacroObservation:
    series_id: str
    day: datetime  # midnight UTC
    value: float


def _parse_csv(series_id: str, text: str) -> list[MacroObservation]:
    lines = text.strip().splitlines()
    out: list[MacroObservation] = []
    for line in lines[1:]:  # skip header row
        parts = line.split(",")
        if len(parts) != 2:
            continue
        raw_day, raw_val = parts[0].strip(), parts[1].strip()
        if raw_val in _MISSING:
            continue
        try:
            day = datetime.strptime(raw_day, "%Y-%m-%d").replace(tzinfo=UTC)
            value = float(raw_val)
        except (ValueError, TypeError):
            continue
        out.append(MacroObservation(series_id=series_id, day=day, value=value))
    return out


class FredAdapter:
    """Fetches daily observations for a set of FRED series over a range."""

    def __init__(
        self, *, series_ids: tuple[str, ...], client: httpx.AsyncClient | None = None
    ) -> None:
        self._series_ids = series_ids
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> FredAdapter:
        if self._client is None:
            # http2=True is load-bearing, not an optimisation: FRED's CDN
            # tarpits HTTP/1.1 clients from datacenter IPs (the request hangs
            # until timeout) while HTTP/2 is served instantly. Requires the
            # `h2` package (httpx[http2]).
            self._client = httpx.AsyncClient(
                timeout=30,
                http2=True,
                headers={"User-Agent": "mentor/1.0 (+local research)"},
            )
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()

    async def _fetch_one(
        self, series_id: str, *, start: datetime, end: datetime, max_retries: int = 5
    ) -> list[MacroObservation]:
        assert self._client is not None
        params = {
            "id": series_id,
            "cosd": start.strftime("%Y-%m-%d"),
            "coed": end.strftime("%Y-%m-%d"),
        }
        last_err = "unknown"
        for attempt in range(max_retries):
            try:
                resp = await self._client.get(_BASE, params=params)
            except httpx.HTTPError as exc:
                raise FredError(f"FRED request failed for {series_id}: {exc}") from exc
            if resp.status_code == 429:
                last_err = "rate limited"
                await asyncio.sleep(_MIN_INTERVAL_S * (attempt + 2))
                continue
            if resp.status_code != 200:
                raise FredError(f"FRED returned {resp.status_code} for {series_id}")
            return _parse_csv(series_id, resp.text)
        raise FredError(f"FRED {last_err} for {series_id} after {max_retries} attempts")

    async def fetch_all(self, *, start: datetime, end: datetime) -> list[MacroObservation]:
        """One list of observations across every configured series."""
        out: list[MacroObservation] = []
        for i, sid in enumerate(self._series_ids):
            if i:
                await asyncio.sleep(_MIN_INTERVAL_S)
            obs = await self._fetch_one(sid, start=start, end=end)
            out.extend(obs)
            log.info("fred.series", series=sid, rows=len(obs))
        return out
