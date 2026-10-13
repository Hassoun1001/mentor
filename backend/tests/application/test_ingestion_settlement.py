"""Ingestion stores only settled bars and corrects ones stored too early.

Regression for the 2026-10-13 production audit: 2,310 hourly and 86 daily
bars had been written mid-period with ``ON CONFLICT DO NOTHING`` and never
corrected; the median stored hourly bar held 23% of the hour's true range.
These tests replay that sequence against an in-memory store.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.application.market.ingestion_service import (
    CORRECTION_REASON,
    IngestionService,
    correction_batch_id,
)
from mentor.application.market.repair import BarRepairService
from mentor.domain.market.adapter import MarketDataAdapter
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.market.settlement import BarCorrection, StoredBar, was_stored_provisional

H = Timeframe.H1
T9 = datetime(2026, 9, 16, 9, tzinfo=UTC)
PIP = Decimal("0.0001")


def _bar(ts: datetime, close: str, source: str = "twelve_data") -> PriceBar:
    c = Decimal(close)
    o = Decimal("1.1000")
    return PriceBar("EURUSD", H, ts, o, max(o, c), min(o, c), c, None, source)


@dataclass(frozen=True)
class _Row:
    symbol: str
    timeframe: str
    ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None
    source: str
    ingested_at: datetime


@dataclass(frozen=True)
class _Revision:
    batch_id: str
    action: str
    reason: str
    old: _Row
    new: PriceBar | None


class _Store:
    """In-memory stand-in with ``PriceBarRepository``'s write semantics."""

    def __init__(self) -> None:
        self.rows: dict[datetime, _Row] = {}
        self.revisions: list[_Revision] = []
        self.clock = T9  # what the database's now() would say on insert

    def _to_row(self, bar: PriceBar, ingested_at: datetime) -> _Row:
        return _Row(
            bar.symbol,
            bar.timeframe.value,
            bar.ts,
            bar.open,
            bar.high,
            bar.low,
            bar.close,
            bar.volume,
            bar.source,
            ingested_at,
        )

    async def upsert_many(self, bars: Sequence[PriceBar]) -> int:
        new = 0
        for b in bars:
            if b.ts not in self.rows:  # ON CONFLICT DO NOTHING
                self.rows[b.ts] = self._to_row(b, self.clock)
                new += 1
        return new

    async def provisional(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Sequence[StoredBar]:
        return [
            r
            for ts, r in sorted(self.rows.items())
            if was_stored_provisional(ts, timeframe, r.ingested_at)
            and (start is None or ts >= start)
            and (end is None or ts < end)
        ]

    async def misaligned(self, *, symbol: str, timeframe: Timeframe) -> Sequence[StoredBar]:
        return [r for ts, r in sorted(self.rows.items()) if ts.minute or ts.second]

    async def apply_corrections(
        self,
        corrections: Sequence[BarCorrection],
        *,
        batch_id: str,
        reason: str,
        now: datetime,
    ) -> int:
        changed = 0
        for c in corrections:
            current = self.rows.get(c.settled.ts)
            if current is None or current.ingested_at != c.stored.ingested_at:
                continue
            self.revisions.append(_Revision(batch_id, "corrected", reason, current, c.settled))
            self.rows[c.settled.ts] = self._to_row(c.settled, now)
            changed += 1
        return changed

    async def remove(
        self, rows: Sequence[StoredBar], *, batch_id: str, reason: str, now: datetime
    ) -> int:
        removed = 0
        for r in rows:
            current = self.rows.pop(r.ts, None)
            if current is not None:
                self.revisions.append(_Revision(batch_id, "removed", reason, current, None))
                removed += 1
        return removed

    async def revert(self, *, batch_id: str, now: datetime) -> tuple[int, int]:
        restored = 0
        for rev in self.revisions:
            if rev.batch_id == batch_id:
                self.rows[rev.old.ts] = rev.old
                restored += 1
        return restored, 0


class _Feed(MarketDataAdapter):
    """Returns whatever the market looks like at ``now`` — including the bar still forming."""

    name = "fake"

    def __init__(self, bars: Sequence[PriceBar]) -> None:
        self.bars = list(bars)
        self.requests: list[tuple[datetime, datetime]] = []

    async def fetch_bars(
        self, *, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> AsyncIterator[PriceBar]:
        self.requests.append((start, end))
        for b in self.bars:
            if start <= b.ts <= end:
                yield b


async def _ingest(store: _Store, bars: Sequence[PriceBar], now: datetime):  # type: ignore[no-untyped-def]
    store.clock = now
    return await IngestionService(adapter=_Feed(bars), repo=store).ingest(
        symbol="EURUSD", timeframe=H, start=now - timedelta(days=1), end=now, now=now
    )


async def test_the_bar_still_forming_is_not_stored() -> None:
    store = _Store()
    at_0905 = T9 + timedelta(minutes=5)
    result = await _ingest(
        store, [_bar(T9 - timedelta(hours=1), "1.1010"), _bar(T9, "1.1003")], at_0905
    )
    assert list(store.rows) == [T9 - timedelta(hours=1)]
    assert (result.persisted, result.skipped_forming) == (1, 1)


async def test_a_feeds_live_tick_between_hours_is_not_stored() -> None:
    store = _Store()
    now = T9 + timedelta(hours=1, minutes=2)
    tick = _bar(T9 + timedelta(minutes=29, seconds=5), "1.1003", source="yahoo")
    result = await _ingest(store, [_bar(T9, "1.1010"), tick], now)
    assert list(store.rows) == [T9]
    assert result.skipped_misaligned == 1


async def test_a_bar_stored_early_is_corrected_on_the_next_fetch_and_logged() -> None:
    # The production sequence: written at 09:05 by the old code, re-fetched at 10:02.
    store = _Store()
    early = _bar(T9, "1.1003")
    store.rows[T9] = store._to_row(early, T9 + timedelta(minutes=5))

    at_1002 = T9 + timedelta(hours=1, minutes=2)
    result = await _ingest(
        store, [_bar(T9, "1.1069"), _bar(T9 + timedelta(hours=1), "1.1070")], at_1002
    )

    assert store.rows[T9].close == Decimal("1.1069")
    assert store.rows[T9].ingested_at == at_1002  # no longer provisional
    assert result.corrected == 1 and result.persisted == 0
    [rev] = store.revisions
    assert rev.action == "corrected" and rev.reason == CORRECTION_REASON
    assert rev.old.close == Decimal("1.1003")  # the replaced value is kept
    assert rev.batch_id == correction_batch_id(H, at_1002) == "ingest:1h:20260916T100200Z"


async def test_a_settled_bar_is_never_rewritten_and_a_repeat_fetch_changes_nothing() -> None:
    store = _Store()
    now = T9 + timedelta(hours=1, minutes=2)
    await _ingest(store, [_bar(T9, "1.1010")], now)
    later = now + timedelta(hours=1)
    result = await _ingest(
        store, [_bar(T9, "1.1012"), _bar(T9 + timedelta(hours=1), "1.1020")], later
    )
    assert store.rows[T9].close == Decimal("1.1010")  # a quiet vendor revision is ignored
    assert result.corrected == 0 and store.revisions == []


async def test_a_correction_only_reaches_the_window_actually_fetched() -> None:
    store = _Store()
    old = T9 - timedelta(days=30)
    store.rows[old] = store._to_row(_bar(old, "1.1003"), old + timedelta(minutes=5))
    now = T9 + timedelta(hours=1, minutes=2)
    await _ingest(store, [_bar(T9, "1.1010")], now)
    assert store.rows[old].close == Decimal("1.1003")  # left for the operator's repair


async def test_repair_plans_without_writing_then_applies_one_reversible_batch() -> None:
    store = _Store()
    hours = [T9 + timedelta(hours=i) for i in range(3)]
    for ts in hours:  # every row captured five minutes in, as in production
        store.rows[ts] = store._to_row(_bar(ts, "1.1001"), ts + timedelta(minutes=5))
    tick = T9 + timedelta(minutes=29, seconds=5)
    store.rows[tick] = store._to_row(_bar(tick, "1.1002", source="yahoo"), tick)
    lost = T9 - timedelta(days=2)  # a provisional row no feed has a settled bar for
    store.rows[lost] = store._to_row(_bar(lost, "1.1001"), lost)
    snapshot = dict(store.rows)

    feed = _Feed([_bar(ts, "1.1040") for ts in hours])
    service = BarRepairService(adapter=feed, repo=store, pip=PIP)
    now = T9 + timedelta(days=1)
    plan = await service.plan(symbol="EURUSD", timeframe=H, now=now)

    assert store.rows == snapshot and store.revisions == []  # plan writes nothing
    assert len(plan.corrections) == 3
    assert [r.ts for r in plan.misaligned] == [tick]
    assert [r.ts for r in plan.unmatched] == [lost]
    assert "3 move more than 0.5 pip" in plan.describe()

    done = await service.apply(plan, now=now, remove_unmatched=False)
    assert (done.corrected, done.removed_misaligned, done.removed_unmatched) == (3, 1, 0)
    assert all(store.rows[ts].close == Decimal("1.1040") for ts in hours)
    assert tick not in store.rows and lost in store.rows
    assert {r.batch_id for r in store.revisions} == {done.batch_id}

    await service.revert(batch_id=done.batch_id, now=now)
    assert store.rows == snapshot


async def test_repair_removes_unmatched_rows_only_when_asked() -> None:
    store = _Store()
    lost = T9 - timedelta(days=2)
    store.rows[lost] = store._to_row(_bar(lost, "1.1001"), lost)
    service = BarRepairService(adapter=_Feed([]), repo=store, pip=PIP)
    now = T9 + timedelta(days=1)
    done = await service.apply(
        await service.plan(symbol="EURUSD", timeframe=H, now=now), now=now, remove_unmatched=True
    )
    assert done.removed_unmatched == 1 and lost not in store.rows
    [rev] = store.revisions
    assert rev.action == "removed" and rev.old.close == Decimal("1.1001") and rev.new is None


async def test_repair_fetches_long_history_in_requests_a_provider_will_serve() -> None:
    store = _Store()
    first = T9 - timedelta(days=400)
    store.rows[first] = store._to_row(_bar(first, "1.1001"), first)
    feed = _Feed([])
    await BarRepairService(adapter=feed, repo=store, pip=PIP).plan(
        symbol="EURUSD", timeframe=H, now=T9
    )
    assert len(feed.requests) > 1
    assert all((end - start) <= timedelta(hours=4000) for start, end in feed.requests)
    assert feed.requests[0][0] <= first and feed.requests[-1][1] == T9
