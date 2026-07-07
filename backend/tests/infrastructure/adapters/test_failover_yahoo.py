"""Tests for the failover chain and Yahoo timestamp normalisation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from mentor.domain.errors import DomainError
from mentor.domain.market.adapter import MarketDataAdapter
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.adapters import (
    AllSourcesFailedError,
    FailoverMarketDataAdapter,
)
from mentor.infrastructure.adapters.yahoo import _normalise_ts


def _bar(ts: datetime, src: str) -> PriceBar:
    return PriceBar(
        symbol="EURUSD",
        timeframe=Timeframe.D1,
        ts=ts,
        open=Decimal("1.1"),
        high=Decimal("1.1"),
        low=Decimal("1.1"),
        close=Decimal("1.1"),
        volume=None,
        source=src,
    )


class _Fake(MarketDataAdapter):
    def __init__(self, name: str, *, fail: bool = False, empty: bool = False) -> None:
        self.name = name
        self._fail = fail
        self._empty = empty

    async def fetch_bars(self, *, symbol, timeframe, start, end) -> AsyncIterator[PriceBar]:  # type: ignore[no-untyped-def]
        if self._fail:
            raise DomainError(f"{self.name} down")
        if self._empty:
            return
        yield _bar(datetime(2026, 1, 1, tzinfo=UTC), self.name)


async def _collect(adapter: MarketDataAdapter) -> list[PriceBar]:
    return [
        b
        async for b in adapter.fetch_bars(
            symbol="EURUSD",
            timeframe=Timeframe.D1,
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 2, 1, tzinfo=UTC),
        )
    ]


@pytest.mark.asyncio
async def test_failover_uses_first_working_source() -> None:
    adapter = FailoverMarketDataAdapter([_Fake("a", fail=True), _Fake("b")])
    bars = await _collect(adapter)
    assert [b.source for b in bars] == ["b"]
    assert adapter.last_source == "b"


@pytest.mark.asyncio
async def test_failover_skips_empty_source() -> None:
    adapter = FailoverMarketDataAdapter([_Fake("a", empty=True), _Fake("b")])
    bars = await _collect(adapter)
    assert [b.source for b in bars] == ["b"]


@pytest.mark.asyncio
async def test_failover_raises_when_all_fail() -> None:
    adapter = FailoverMarketDataAdapter([_Fake("a", fail=True), _Fake("b", empty=True)])
    with pytest.raises(AllSourcesFailedError):
        await _collect(adapter)


def test_yahoo_daily_ts_snaps_to_utc_midnight() -> None:
    # 23:00 UTC on 21 Jun (London midnight, BST) is the 22 Jun trading day.
    ts = int(datetime(2026, 6, 21, 23, 0, tzinfo=UTC).timestamp())
    assert _normalise_ts(ts, Timeframe.D1) == datetime(2026, 6, 22, tzinfo=UTC)
    # A 00:00 UTC winter bar stays on its own date.
    ts_winter = int(datetime(2026, 1, 15, 0, 0, tzinfo=UTC).timestamp())
    assert _normalise_ts(ts_winter, Timeframe.D1) == datetime(2026, 1, 15, tzinfo=UTC)


def test_yahoo_intraday_ts_passes_through() -> None:
    ts = int(datetime(2026, 6, 21, 14, 30, tzinfo=UTC).timestamp())
    assert _normalise_ts(ts, Timeframe.H1) == datetime(2026, 6, 21, 14, 30, tzinfo=UTC)
