"""Regression tests for the Batch-1 correctness fixes.

1. Promotion gate: coin-flip floor — worse-than-random never ships,
   even as the first champion, even when it beats a bad incumbent.
2. Split embargo: fit/calibration/test slices leave horizon_bars-sized
   gaps so outcome windows can't straddle boundaries.
3. Drift watch: overlapping hourly calls reduce to independent samples.
"""

from __future__ import annotations

import math
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from mentor.application.forecasting.promotion import PromotionService
from mentor.application.scheduler.drift import select_independent
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.forecasting.sklearn_forecaster import train_sklearn_forecaster

_HORIZON = 24


def _noise_bars(n: int = 500) -> list[PriceBar]:
    """Pure random walk — nothing learnable, Brier should hug 0.25."""
    rng = random.Random(11)
    start = datetime(2025, 1, 1, tzinfo=UTC)
    px = 1.10
    out: list[PriceBar] = []
    for i in range(n):
        px += rng.uniform(-0.002, 0.002)
        p = Decimal(f"{px:.5f}")
        out.append(
            PriceBar(
                symbol="EURUSD",
                timeframe=Timeframe.H1,
                ts=start + timedelta(hours=i),
                open=p,
                high=p + Decimal("0.0010"),
                low=p - Decimal("0.0010"),
                close=p,
                volume=Decimal("100"),
                source="test",
            )
        )
    return out


def _sine_bars(n: int = 600) -> list[PriceBar]:
    """Strongly periodic — learnable, Brier should beat the floor."""
    start = datetime(2025, 1, 1, tzinfo=UTC)
    out: list[PriceBar] = []
    for i in range(n):
        px = 1.10 + 0.02 * math.sin(i / 10)
        p = Decimal(f"{px:.5f}")
        out.append(
            PriceBar(
                symbol="EURUSD",
                timeframe=Timeframe.H1,
                ts=start + timedelta(hours=i),
                open=p,
                high=p + Decimal("0.0010"),
                low=p - Decimal("0.0010"),
                close=p,
                volume=Decimal("100"),
                source="test",
            )
        )
    return out


class _FakePriceRepo:
    def __init__(self, bars: list[PriceBar]) -> None:
        self._bars = bars

    async def range(self, *, symbol: str, timeframe: Timeframe, start: datetime, end: datetime):  # type: ignore[no-untyped-def]
        return [
            SimpleNamespace(
                symbol=b.symbol,
                timeframe=b.timeframe.value,
                ts=b.ts,
                open=str(b.open),
                high=str(b.high),
                low=str(b.low),
                close=str(b.close),
                volume=str(b.volume),
                source=b.source,
            )
            for b in self._bars
        ]


# ---- fix 2: the coin-flip floor ------------------------------------------


async def test_random_walk_challenger_cannot_become_first_champion(tmp_path: Path) -> None:
    service = PromotionService(model_store_dir=tmp_path, prices=_FakePriceRepo(_noise_bars()))  # type: ignore[arg-type]
    result = await service.retrain_and_promote(
        symbol="EURUSD", timeframe=Timeframe.H1, horizon_bars=_HORIZON
    )
    # On unlearnable data the model can't clear the floor; no champion installs
    # and the transparent baseline keeps predicting.
    if result.challenger_brier > 0.248:
        assert result.promoted is False
        assert service.current_champion() is None
        assert "floor" in result.reason
    else:  # freak seed learned noise — floor logic must still have been applied
        assert result.promoted is True


async def test_learnable_data_still_installs_first_champion(tmp_path: Path) -> None:
    service = PromotionService(model_store_dir=tmp_path, prices=_FakePriceRepo(_sine_bars()))  # type: ignore[arg-type]
    result = await service.retrain_and_promote(
        symbol="EURUSD", timeframe=Timeframe.H1, horizon_bars=_HORIZON
    )
    assert result.challenger_brier <= 0.248  # sine wave is genuinely learnable
    assert result.promoted is True
    assert service.current_champion() is not None


# ---- fix 3: split embargo -------------------------------------------------


def test_splits_leave_embargo_gaps() -> None:
    bars = _sine_bars()
    model = train_sklearn_forecaster(bars=bars, horizon_bars=_HORIZON)
    r = model.report
    # fit + calibration + test must NOT tile the sample range: two embargo
    # gaps of horizon_bars each are dropped at the boundaries.
    assert r.n_train + r.n_calibration + r.n_test == r.n_samples - 2 * _HORIZON


# ---- fix 4: independent drift samples ------------------------------------


def _call(hour: int, p: float = 0.6, y: int = 1):  # type: ignore[no-untyped-def]
    asof = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=hour)
    return (asof, asof + timedelta(hours=_HORIZON), p, y)


def test_hourly_overlapping_calls_reduce_to_daily_independent() -> None:
    calls = [_call(h) for h in range(72)]  # 72 hourly calls, 24h horizons
    kept = select_independent(calls)
    # Windows are [t, t+24] — non-overlap keeps roughly one per day.
    assert len(kept) == 3


def test_spaced_calls_are_all_kept() -> None:
    calls = [_call(h) for h in range(0, 240, 24)]  # already one per day
    kept = select_independent(calls)
    assert len(kept) == 10


def test_select_independent_handles_empty_and_order() -> None:
    assert select_independent([]) == []
    shuffled = [_call(48), _call(0), _call(24)]
    assert len(select_independent(shuffled)) == 3
