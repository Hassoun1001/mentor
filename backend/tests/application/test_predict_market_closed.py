"""The loop makes no forecast while the market is closed."""

from __future__ import annotations

from typing import Any

import pytest

from mentor.application.scheduler import service as scheduler_service
from mentor.application.scheduler.service import LoopScheduler
from mentor.domain.market.bars import Timeframe


class _Health:
    def __init__(self) -> None:
        self.beats: list[tuple[str, bool, str]] = []

    def beat(self, job: str, *, ok: bool, note: str) -> None:
        self.beats.append((job, ok, note))


async def test_closed_market_skips_the_forecast(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _must_not_run(_: Timeframe) -> tuple[bool, str]:
        raise AssertionError("a closed market must not reach the forecast path")

    monkeypatch.setattr(scheduler_service, "fx_market_open", lambda _: False)
    loop: Any = LoopScheduler.__new__(LoopScheduler)
    loop._settings = object()
    loop._health = _Health()
    loop._quality_check = _must_not_run

    result = await loop._predict_lane(tf=Timeframe.H1, horizon_bars=24, lane="h1", job="predict")

    assert result is None
    assert loop._health.beats == [("predict", True, "market closed: no forecast")]
