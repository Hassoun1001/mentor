"""Finnhub calendar adapter — a plan-gated key must fail clearly, not obscurely.

The economic calendar is a paid Finnhub endpoint, so a valid free-tier key
returns 403. That must surface as a clear, non-retryable message (the
event-freeze simply stays off), never a bare HTTP error retried four times.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest

from mentor.domain.errors import DomainError
from mentor.infrastructure.adapters.calendar.finnhub import FinnhubCalendarAdapter


def _adapter_returning(status: int, json_body: object) -> FinnhubCalendarAdapter:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=json_body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return FinnhubCalendarAdapter(api_key="free-tier-key", client=client)


async def _fetch(adapter: FinnhubCalendarAdapter) -> list[object]:
    now = datetime(2026, 7, 31, tzinfo=UTC)
    return [e async for e in adapter.fetch(since=now, until=now)]


@pytest.mark.parametrize("status", [401, 403])
async def test_a_plan_gated_key_raises_a_clear_domain_error(status: int) -> None:
    adapter = _adapter_returning(status, {"error": "no access"})
    with pytest.raises(DomainError) as exc:
        await _fetch(adapter)
    assert "paid Finnhub feature" in str(exc.value)
    assert "event-freeze" in str(exc.value)
    await adapter.aclose()


async def test_a_working_key_yields_events() -> None:
    body = {
        "economicCalendar": {
            "event": [
                {
                    "time": "2026-07-31 12:30:00",
                    "country": "US",
                    "event": "Nonfarm Payrolls",
                    "impact": "high",
                    "estimate": "180K",
                    "prev": "175K",
                    "actual": None,
                }
            ]
        }
    }
    adapter = _adapter_returning(200, body)
    events = await _fetch(adapter)
    assert len(events) == 1
    assert events[0].name == "Nonfarm Payrolls"
    await adapter.aclose()
