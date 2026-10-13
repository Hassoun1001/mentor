"""When a stored bar can be trusted — and how a provisional one is put right.

A bar's open, high, low and close are only final once its period has
elapsed. Every feed will hand back the bar that is still forming, and
until October 2026 ingestion stored it and never looked at it again: the
row was written with ``ON CONFLICT DO NOTHING``, so the settled version
fetched an hour later was discarded. Production audit, 2026-10-13: every
hourly bar since mid-July (2,310) and 86 daily bars had been captured
mid-period, most within ten minutes of opening. Against a fresh fetch, the
median stored hourly bar held 23% of the hour's real range, and 774 were
more than five pips off. Every model trained since then, every back-test
and every outcome graded off those rows read prices that never closed.

Three rules, all pure, so ingestion and the one-off repair share them:

1. Only a **settled, aligned** bar is stored. Settled: its period has
   fully elapsed. Aligned: it is stamped on its timeframe's boundary.
   Yahoo labels its live hourly bar with the last trade's time (10:29:05),
   which put 275 extra rows between real hours.
2. A stored bar written before its period closed is **provisional**. The
   evidence is its own ``ingested_at``; no extra column is needed.
3. A provisional bar is replaced by the settled one the first time it is
   fetched. A settled bar is never overwritten by ingestion: feeds differ
   by fractions of a pip and revise quietly, and history that shifts every
   time it is re-read is history nothing can be tested against.

Point-in-time safety is the caller's half: a prediction keeps the
``asof_close`` it was made from and a resolved outcome keeps its
``realised_close``. Correcting a bar changes what later reads see, never a
record already written.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol

from mentor.domain.market.bars import PriceBar, Timeframe


def closes_at(ts: datetime, timeframe: Timeframe) -> datetime:
    """The instant a bar stamped ``ts`` stops changing."""
    return ts + timedelta(seconds=timeframe.seconds)


def is_settled(ts: datetime, timeframe: Timeframe, now: datetime) -> bool:
    """True once the bar's whole period lies in the past."""
    return closes_at(ts, timeframe) <= now


def is_aligned(ts: datetime, timeframe: Timeframe) -> bool:
    """True when ``ts`` sits on the timeframe's UTC boundary.

    Every timeframe divides a UTC day, so the epoch is a valid origin and
    a daily bar must be stamped at UTC midnight.
    """
    return ts.timestamp() % timeframe.seconds == 0


def was_stored_provisional(ts: datetime, timeframe: Timeframe, ingested_at: datetime) -> bool:
    """True when the row was written before its period closed."""
    return ingested_at < closes_at(ts, timeframe)


class StoredBar(Protocol):
    """What the correction rules read from a stored row (the ORM satisfies it)."""

    @property
    def symbol(self) -> str: ...
    @property
    def timeframe(self) -> str: ...
    @property
    def ts(self) -> datetime: ...
    @property
    def open(self) -> Decimal: ...
    @property
    def high(self) -> Decimal: ...
    @property
    def low(self) -> Decimal: ...
    @property
    def close(self) -> Decimal: ...
    @property
    def volume(self) -> Decimal | None: ...
    @property
    def source(self) -> str: ...
    @property
    def ingested_at(self) -> datetime: ...


@dataclass(frozen=True, slots=True)
class Screened:
    """A fetch split into what may be stored and what may not."""

    settled: tuple[PriceBar, ...]
    forming: int
    misaligned: int


def screen(bars: Iterable[PriceBar], *, now: datetime) -> Screened:
    """Keep the bars that are safe to store; count the rest so it is visible."""
    kept: list[PriceBar] = []
    forming = misaligned = 0
    for bar in bars:
        if not is_aligned(bar.ts, bar.timeframe):
            misaligned += 1
        elif not is_settled(bar.ts, bar.timeframe, now):
            forming += 1
        else:
            kept.append(bar)
    return Screened(settled=tuple(kept), forming=forming, misaligned=misaligned)


@dataclass(frozen=True, slots=True)
class BarCorrection:
    """A provisional row and the settled bar that replaces it."""

    stored: StoredBar
    settled: PriceBar

    @property
    def max_move(self) -> Decimal:
        """Largest absolute change across open, high, low and close."""
        s, n = self.stored, self.settled
        return max(
            abs(Decimal(s.open) - n.open),
            abs(Decimal(s.high) - n.high),
            abs(Decimal(s.low) - n.low),
            abs(Decimal(s.close) - n.close),
        )


def plan_corrections(
    stored: Sequence[StoredBar], settled: Sequence[PriceBar], timeframe: Timeframe
) -> list[BarCorrection]:
    """Pair every provisional stored row with the settled bar that replaces it.

    Rows stored after their period closed are never paired, whatever the
    fresh fetch says (rule 3). A provisional row is replaced even when the
    numbers happen to agree, so it stops being provisional and the audit
    log shows it was checked.
    """
    by_ts = {b.ts: b for b in settled if b.timeframe is timeframe}
    out: list[BarCorrection] = []
    for row in stored:
        if not was_stored_provisional(row.ts, timeframe, row.ingested_at):
            continue
        fresh = by_ts.get(row.ts)
        if fresh is not None:
            out.append(BarCorrection(stored=row, settled=fresh))
    return out
