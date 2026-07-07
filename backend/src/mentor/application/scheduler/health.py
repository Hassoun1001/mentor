"""Loop observability — job heartbeats and notable events.

A 24/7 loop that can't be observed is a black box you learn to distrust.
This registry keeps, in memory, the last outcome of every job (when it
ran, whether it succeeded, and a one-line note) plus a ring buffer of
notable events (drift verdicts, promotions, quality skips, source
failures). The scheduler updates it on every tick and `status()` exposes
it, so the UI can show at a glance that the system is alive — or exactly
which part of it isn't.

In-memory is deliberate: heartbeats describe *this process*. Durable
history that must survive restarts (champion promotions) is persisted
separately as `promotions.jsonl` in the model store.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime

_MAX_EVENTS = 50


@dataclass(frozen=True, slots=True)
class Heartbeat:
    job: str
    at: datetime
    ok: bool
    note: str


@dataclass(frozen=True, slots=True)
class LoopEvent:
    kind: str  # drift_detected | promotion | quality_skip | ingest_error | alert
    at: datetime
    detail: str


class LoopHealth:
    def __init__(self, *, max_events: int = _MAX_EVENTS) -> None:
        self._beats: dict[str, Heartbeat] = {}
        self._events: deque[LoopEvent] = deque(maxlen=max_events)

    def beat(self, job: str, *, ok: bool, note: str) -> None:
        self._beats[job] = Heartbeat(job=job, at=datetime.now(UTC), ok=ok, note=note)

    def event(self, kind: str, detail: str) -> None:
        self._events.appendleft(LoopEvent(kind=kind, at=datetime.now(UTC), detail=detail))

    def snapshot(self) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        """(heartbeats, events) as plain dicts, newest events first."""
        beats = [
            {"job": b.job, "at": b.at.isoformat(), "ok": b.ok, "note": b.note}
            for b in sorted(self._beats.values(), key=lambda b: b.job)
        ]
        events: list[dict[str, object]] = [
            {"kind": e.kind, "at": e.at.isoformat(), "detail": e.detail} for e in self._events
        ]
        return beats, events
