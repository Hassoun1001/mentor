"""Voiding calls made from closed-market bars."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from mentor.application.forecasting.regrade import ClosedMarketVoidService, LiveCall
from mentor.domain.forecasting.outcome import VOID_CLOSED_MARKET_REASON


@dataclass
class _Call:
    timeframe: str
    asof: datetime


class _Store:
    def __init__(self, calls: list[_Call]) -> None:
        self.calls = calls
        self.voided: list[LiveCall] = []
        self.reason = ""

    async def live_calls(self) -> Sequence[LiveCall]:
        return self.calls

    async def void_calls(
        self, calls: Sequence[LiveCall], *, batch_id: str, reason: str, now: datetime
    ) -> int:
        self.voided = list(calls)
        self.reason = reason
        return len(calls)


async def test_only_calls_started_on_a_closed_market_bar_are_voided() -> None:
    open_thursday = _Call("1h", datetime(2026, 11, 5, 12, tzinfo=UTC))
    due_at_weekend = _Call("1h", datetime(2026, 11, 6, 12, tzinfo=UTC))
    saturday = _Call("1h", datetime(2026, 11, 7, 12, tzinfo=UTC))
    daily_sunday = _Call("1d", datetime(2026, 11, 8, tzinfo=UTC))
    store = _Store([open_thursday, due_at_weekend, saturday, daily_sunday])
    service = ClosedMarketVoidService(predictions=store)

    planned = await service.plan()

    assert list(planned) == [saturday, daily_sunday]
    outcome = await service.apply(planned, now=datetime(2026, 11, 8, 12, tzinfo=UTC))
    assert outcome.changed == 2
    assert outcome.batch_id == "void:20261108T120000Z"
    assert store.reason == VOID_CLOSED_MARKET_REASON
