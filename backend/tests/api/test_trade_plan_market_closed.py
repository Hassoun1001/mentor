"""A closed market has no price to trade, so the plan must not offer one.

The feed keeps printing quotes through the weekend and the model keeps
reading them, so a directional call with fresh-looking data is exactly what
the ticket would otherwise show on a Saturday.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from mentor.api.v1 import forecasting as endpoint
from mentor.config import Settings
from mentor.domain.forecasting.forecast import Direction, Forecast
from mentor.domain.forecasting.volatility import VolForecast, VolRegime
from mentor.domain.market.bars import Timeframe

_SATURDAY_NOON = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
_TUESDAY_NOON = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)
_FRIDAY_LAST_OPEN_MINUTE = datetime(2026, 11, 6, 21, 59, tzinfo=UTC)
_FRIDAY_AT_THE_CLOSE = datetime(2026, 11, 6, 22, 0, tzinfo=UTC)
_SUNDAY_BEFORE_REOPEN = datetime(2026, 11, 8, 21, 59, tzinfo=UTC)
_SUNDAY_AT_THE_REOPEN = datetime(2026, 11, 8, 22, 0, tzinfo=UTC)


def _short_forecast(asof: datetime) -> Forecast:
    """A call confident enough that an open market gets a real ticket."""
    return Forecast(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        asof=asof,
        asof_close=Decimal("1.11404"),
        horizon_bars=24,
        p_up=Decimal("0.35"),
        confidence=Decimal("0.30"),
        direction=Direction.SHORT,
        model_name="baseline",
        reasoning="Short-term momentum is falling.",
        features={},
    )


def _vol_forecast(asof: datetime) -> VolForecast:
    return VolForecast(
        symbol="EURUSD",
        timeframe=Timeframe.D1,
        asof=asof,
        asof_close=Decimal("1.11404"),
        horizon_bars=1,
        expected_vol=Decimal("0.004"),
        expected_range_pips=Decimal("40"),
        percentile_vs_history=Decimal("0.5"),
        regime=VolRegime.NORMAL,
        model_name="ewma",
        reasoning="Volatility is ordinary.",
    )


@pytest.fixture
def plan_at(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Any:
    """Build the plan as the real endpoint would at a chosen moment."""

    async def build(now: datetime) -> endpoint.TradePlanResponse:
        asof = now - timedelta(hours=2)

        class _Clock(datetime):
            @classmethod
            def now(cls, tz: Any = None) -> datetime:  # type: ignore[override]
                return now.astimezone(tz)

        class _ForecastService:
            def __init__(self, **_: Any) -> None:
                pass

            async def predict(self, **_: Any) -> SimpleNamespace:
                return SimpleNamespace(forecast=_short_forecast(asof))

        class _VolService:
            def __init__(self, **_: Any) -> None:
                pass

            async def predict_vol(self, **_: Any) -> SimpleNamespace:
                return SimpleNamespace(forecast=_vol_forecast(asof))

        monkeypatch.setattr(endpoint, "datetime", _Clock)
        monkeypatch.setattr(endpoint, "ForecastService", _ForecastService)
        monkeypatch.setattr(endpoint, "VolService", _VolService)
        return await endpoint.trade_plan(
            session=None,  # type: ignore[arg-type]
            settings=Settings(db_password="x", model_store_dir=str(tmp_path)),
            balance=Decimal("10000"),
            risk_percent=Decimal("1"),
            reward_multiple=Decimal("2"),
        )

    return build


async def test_a_saturday_call_offers_no_trade_and_says_why(plan_at: Any) -> None:
    plan = await plan_at(_SATURDAY_NOON)

    assert plan.stance == "stand_aside"
    assert plan.levels is None
    assert plan.size is None
    assert plan.management is None
    assert plan.realism is None
    assert "market is closed" in plan.headline


async def test_the_same_call_on_a_weekday_still_gets_a_ticket(plan_at: Any) -> None:
    plan = await plan_at(_TUESDAY_NOON)

    assert plan.stance == "short"
    assert plan.levels is not None
    assert plan.size is not None
    assert "market is closed" not in plan.headline


@pytest.mark.parametrize(
    ("now", "stance"),
    [
        (_FRIDAY_LAST_OPEN_MINUTE, "short"),
        (_FRIDAY_AT_THE_CLOSE, "stand_aside"),
        (_SUNDAY_BEFORE_REOPEN, "stand_aside"),
        (_SUNDAY_AT_THE_REOPEN, "short"),
    ],
)
async def test_the_guard_follows_the_weekly_close_and_reopen(
    plan_at: Any, now: datetime, stance: str
) -> None:
    assert (await plan_at(now)).stance == stance


async def test_a_quiet_closed_market_is_not_reported_as_a_broken_feed(plan_at: Any) -> None:
    plan = await plan_at(_SATURDAY_NOON)

    assert plan.data_stale is False
    assert plan.warnings == []
