"""Finnhub economic-calendar adapter.

Finnhub's `/calendar/economic` endpoint returns scheduled releases by
date range, with a `impact` field (Low/Medium/High). We map that to the
domain's `ImpactLevel` and produce a stable `external_id` from the
country + event-name + timestamp so re-fetching is idempotent.
"""

from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any, Final

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from mentor.domain.calendar.adapter import EconomicCalendarAdapter, RawEconomicEvent
from mentor.domain.calendar.event import ImpactLevel
from mentor.domain.errors import DomainError


class FinnhubError(DomainError):
    pass


_IMPACT_MAP: Final[dict[str, ImpactLevel]] = {
    "low": ImpactLevel.LOW,
    "medium": ImpactLevel.MEDIUM,
    "high": ImpactLevel.HIGH,
}


class FinnhubCalendarAdapter(EconomicCalendarAdapter):
    name = "finnhub"
    _BASE_URL: Final = "https://finnhub.io/api/v1"

    def __init__(self, *, api_key: str, client: httpx.AsyncClient | None = None) -> None:
        if not api_key:
            raise ValueError("FinnhubCalendarAdapter requires an api_key")
        self._api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=15.0)

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
            params={**params, "token": self._api_key},
        )
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise FinnhubError("unexpected response shape from Finnhub")
        return body

    async def fetch(self, *, since: datetime, until: datetime) -> AsyncIterator[RawEconomicEvent]:
        params = {
            "from": since.astimezone(UTC).strftime("%Y-%m-%d"),
            "to": until.astimezone(UTC).strftime("%Y-%m-%d"),
        }
        body = await self._get("/calendar/economic", params)
        events = (body.get("economicCalendar") or {}).get("event") or []
        for event in events:
            ts = _parse_dt(event.get("time"))
            if ts is None:
                continue
            impact = _IMPACT_MAP.get(str(event.get("impact", "")).lower())
            if impact is None:
                continue
            country = str(event.get("country") or "??").upper()[:8]
            name = str(event.get("event") or "(unnamed)")
            external_id = _stable_id(source="finnhub", ts=ts, country=country, name=name)
            yield RawEconomicEvent(
                source="finnhub",
                external_id=external_id,
                ts=ts,
                name=name,
                country=country,
                impact=impact,
                forecast=_coerce_str(event.get("estimate")),
                previous=_coerce_str(event.get("prev")),
                actual=_coerce_str(event.get("actual")),
            )


def _coerce_str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace(" ", "T")
    if "T" not in text:
        # bare YYYY-MM-DD — treat as midnight UTC
        text += "T00:00:00"
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _stable_id(*, source: str, ts: datetime, country: str, name: str) -> str:
    fingerprint = f"{source}|{ts.isoformat()}|{country}|{name}"
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
