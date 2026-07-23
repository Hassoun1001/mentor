"""The resolver must not lose predictions that expire into a closed market."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from mentor.application.forecasting.resolver import resolve_pending_predictions
from mentor.domain.market.bars import PriceBar, Timeframe

_NOW = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)


def _pending(horizon_at: datetime) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        symbol="EURUSD",
        timeframe="1h",
        horizon_at=horizon_at,
    )


def _bar(ts: datetime, close: str) -> PriceBar:
    p = Decimal(close)
    return PriceBar(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        ts=ts,
        open=p,
        high=p,
        low=p,
        close=p,
        volume=Decimal("1"),
        source="test",
    )


class _FakePredictions:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self._rows = rows
        self.resolved: list[tuple[uuid.UUID, Decimal]] = []

    async def unresolved_due_by(self, _now: datetime) -> list[SimpleNamespace]:
        return self._rows

    async def resolve(
        self, pid: uuid.UUID, *, realised_close: Decimal, resolved_at: datetime
    ) -> None:
        self.resolved.append((pid, realised_close))


class _FakePrices:
    def __init__(self, bars: list[PriceBar]) -> None:
        self._bars = bars

    async def range(
        self, *, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> list[PriceBar]:
        return [b for b in self._bars if start <= b.ts <= end]


@pytest.mark.asyncio
async def test_a_horizon_inside_the_weekend_resolves_at_the_reopen() -> None:
    """Regression: FX prints nothing between Friday ~21:00 and Sunday ~23:00,
    so a 24-hour call opened late in the week expired into silence. The
    resolver searched two bars either side, found none, and left it pending
    forever. Ninety predictions were stuck this way in production — and
    because only late-week calls were affected, the surviving track record
    was biased toward mid-week rather than merely smaller."""
    horizon = datetime(2026, 7, 18, 0, 21, tzinfo=UTC)  # Saturday, market shut
    prices = _FakePrices(
        [
            _bar(datetime(2026, 7, 17, 21, 0, tzinfo=UTC), "1.1700"),  # Friday close
            _bar(datetime(2026, 7, 19, 23, 0, tzinfo=UTC), "1.1750"),  # Sunday open
        ]
    )
    preds = _FakePredictions([_pending(horizon)])

    result = await resolve_pending_predictions(
        predictions=preds, prices=prices, now=_NOW
    )

    assert result.resolved == 1
    assert result.still_pending == 0
    # Graded at the reopen, not the stale Friday close — that is the price
    # you would actually have got holding through the weekend.
    assert preds.resolved[0][1] == Decimal("1.1750")


@pytest.mark.asyncio
async def test_a_normal_horizon_still_uses_its_own_bar() -> None:
    horizon = datetime(2026, 7, 22, 10, 0, tzinfo=UTC)
    prices = _FakePrices(
        [
            _bar(datetime(2026, 7, 22, 9, 0, tzinfo=UTC), "1.1000"),
            _bar(horizon, "1.1100"),
            _bar(datetime(2026, 7, 22, 11, 0, tzinfo=UTC), "1.1200"),
        ]
    )
    preds = _FakePredictions([_pending(horizon)])

    await resolve_pending_predictions(predictions=preds, prices=prices, now=_NOW)
    assert preds.resolved[0][1] == Decimal("1.1100")


@pytest.mark.asyncio
async def test_a_bar_stamped_just_before_the_horizon_is_accepted() -> None:
    """Feeds round to bar boundaries, so the fill can land marginally early."""
    horizon = datetime(2026, 7, 22, 10, 5, tzinfo=UTC)
    prices = _FakePrices([_bar(datetime(2026, 7, 22, 10, 0, tzinfo=UTC), "1.1000")])
    preds = _FakePredictions([_pending(horizon)])

    await resolve_pending_predictions(predictions=preds, prices=prices, now=_NOW)
    assert preds.resolved[0][1] == Decimal("1.1000")


@pytest.mark.asyncio
async def test_a_data_outage_leaves_the_prediction_pending() -> None:
    """Past four days the silence is a broken feed, not a closed market —
    grading a 24-hour call against next week's price would be fiction."""
    horizon = datetime(2026, 7, 10, 0, 0, tzinfo=UTC)
    prices = _FakePrices([_bar(datetime(2026, 7, 20, 0, 0, tzinfo=UTC), "1.1900")])
    preds = _FakePredictions([_pending(horizon)])

    result = await resolve_pending_predictions(
        predictions=preds, prices=prices, now=_NOW
    )
    assert result.resolved == 0
    assert result.still_pending == 1
    assert preds.resolved == []


@pytest.mark.asyncio
async def test_nothing_pending_is_not_an_error() -> None:
    result = await resolve_pending_predictions(
        predictions=_FakePredictions([]), prices=_FakePrices([]), now=_NOW
    )
    assert (result.examined, result.resolved, result.still_pending) == (0, 0, 0)
