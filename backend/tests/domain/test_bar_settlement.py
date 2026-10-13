"""When a stored bar can be trusted, and how a provisional one is put right.

Regression for the 2026-10-13 production audit: ingestion stored the bar
still forming (and Yahoo's live tick, stamped between hours) and never
corrected it. See ``mentor/domain/market/settlement.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.market.settlement import (
    closes_at,
    is_aligned,
    is_settled,
    plan_corrections,
    screen,
    was_stored_provisional,
)

H = Timeframe.H1
T9 = datetime(2026, 9, 16, 9, tzinfo=UTC)


def _bar(ts: datetime, close: str, tf: Timeframe = H) -> PriceBar:
    c = Decimal(close)
    o = Decimal("1.1000")
    return PriceBar("EURUSD", tf, ts, o, max(o, c), min(o, c), c, None, "twelve_data")


@dataclass(frozen=True)
class _Row:
    ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    ingested_at: datetime
    volume: Decimal | None = None
    source: str = "twelve_data"
    symbol: str = "EURUSD"
    timeframe: str = "1h"


def _row(ts: datetime, close: str, ingested_at: datetime) -> _Row:
    c = Decimal(close)
    o = Decimal("1.1000")
    return _Row(ts, o, max(o, c), min(o, c), c, ingested_at)


def test_a_bar_is_settled_exactly_when_its_period_ends() -> None:
    assert closes_at(T9, H) == T9 + timedelta(hours=1)
    assert not is_settled(T9, H, T9 + timedelta(minutes=59, seconds=59))
    assert is_settled(T9, H, T9 + timedelta(hours=1))
    day = datetime(2026, 9, 16, tzinfo=UTC)
    assert not is_settled(day, Timeframe.D1, datetime(2026, 9, 16, 23, 59, tzinfo=UTC))
    assert is_settled(day, Timeframe.D1, datetime(2026, 9, 17, tzinfo=UTC))


@pytest.mark.parametrize(
    ("ts", "tf", "aligned"),
    [
        (T9, H, True),
        (datetime(2026, 7, 16, 10, 29, 5, tzinfo=UTC), H, False),  # Yahoo's live tick
        (datetime(2026, 9, 16, tzinfo=UTC), Timeframe.D1, True),
        (datetime(2026, 9, 15, 23, tzinfo=UTC), Timeframe.D1, False),  # exchange-local midnight
    ],
)
def test_alignment_is_judged_against_the_utc_boundary(
    ts: datetime, tf: Timeframe, aligned: bool
) -> None:
    assert is_aligned(ts, tf) is aligned


def test_a_row_written_before_its_close_is_provisional() -> None:
    # The production pattern: the 09:00 bar written at 09:05 by an hourly ingest.
    assert was_stored_provisional(T9, H, T9 + timedelta(minutes=5))
    assert not was_stored_provisional(T9, H, T9 + timedelta(hours=1, minutes=2))


def test_screen_keeps_only_settled_aligned_bars_and_counts_the_rest() -> None:
    now = T9 + timedelta(hours=2, minutes=2)
    fetched = [
        _bar(T9, "1.1010"),
        _bar(T9 + timedelta(hours=1), "1.1020"),
        _bar(T9 + timedelta(hours=2), "1.1030"),  # still forming at 11:02
        _bar(T9 + timedelta(hours=1, minutes=29, seconds=5), "1.1015"),  # live tick
    ]
    s = screen(fetched, now=now)
    assert [b.ts for b in s.settled] == [T9, T9 + timedelta(hours=1)]
    assert (s.forming, s.misaligned) == (1, 1)


def test_a_provisional_row_is_replaced_by_its_settled_bar() -> None:
    # Stored at 09:05 with five minutes of the hour; the hour actually closed
    # 66 pips higher (the worst case found in production, 2026-09-16 18:00).
    stored = [_row(T9, "1.1003", ingested_at=T9 + timedelta(minutes=5))]
    settled = [_bar(T9, "1.1069")]
    [c] = plan_corrections(stored, settled, H)
    assert c.settled.close == Decimal("1.1069")
    assert c.max_move == Decimal("0.0066")


def test_a_settled_row_is_never_overwritten_whatever_the_feed_says_later() -> None:
    stored = [_row(T9, "1.1010", ingested_at=T9 + timedelta(hours=1, minutes=2))]
    assert plan_corrections(stored, [_bar(T9, "1.1011")], H) == []


def test_a_provisional_row_is_confirmed_even_when_the_numbers_agree() -> None:
    # Otherwise it would stay provisional, and be re-checked, forever.
    stored = [_row(T9, "1.1010", ingested_at=T9 + timedelta(minutes=5))]
    [c] = plan_corrections(stored, [_bar(T9, "1.1010")], H)
    assert c.max_move == 0


def test_a_provisional_row_without_a_settled_bar_is_left_for_the_operator() -> None:
    stored = [_row(T9, "1.1010", ingested_at=T9 + timedelta(minutes=5))]
    assert plan_corrections(stored, [_bar(T9 + timedelta(hours=1), "1.1010")], H) == []


def test_a_bar_of_another_timeframe_never_corrects_a_row() -> None:
    midnight = datetime(2026, 9, 16, tzinfo=UTC)
    stored = [_row(midnight, "1.1010", ingested_at=midnight + timedelta(minutes=5))]
    daily = _bar(midnight, "1.1050", tf=Timeframe.D1)  # same stamp, a whole day's range
    assert plan_corrections(stored, [daily], H) == []
