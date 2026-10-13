"""Live recalibration wiring: whose calls count, what is in force, and that
inference actually applies it.

Fixtures are deterministic stand-ins for prediction rows and repositories —
no database, no RNG.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from mentor.application.forecasting.inference_service import ForecastService
from mentor.application.forecasting.live_calibration import (
    LiveCalibrationStore,
    champion_live_calls,
    parse_promoted_at,
)
from mentor.application.forecasting.promotion import PromotionService
from mentor.domain.forecasting.forecast import Direction, Forecast
from mentor.domain.forecasting.live_recalibration import LiveRecalibration, recalibrate
from mentor.domain.market.bars import Timeframe

_PROMOTED = datetime(2026, 10, 6, 12, tzinfo=UTC)
_CHAMPION_MODEL = "regime_adjusted(sklearn_hgb(h=24,macro))"


def _row(
    asof: datetime,
    p_up: str,
    outcome: int | None,
    *,
    model: str = _CHAMPION_MODEL,
    p_up_model: str | None = None,
    horizon_hours: int = 24,
) -> SimpleNamespace:
    return SimpleNamespace(
        asof=asof,
        horizon_at=asof + timedelta(hours=horizon_hours),
        model_name=model,
        p_up=Decimal(p_up),
        p_up_model=Decimal(p_up_model) if p_up_model is not None else None,
        realised_outcome=outcome,
        direction="long" if Decimal(p_up) >= Decimal("0.55") else "neutral",
        confidence=abs(Decimal(p_up) - Decimal("0.5")) * 2,
        features_json="{}",
        resolved_at=asof + timedelta(hours=horizon_hours) if outcome is not None else None,
    )


def _daily_overconfident(days: int) -> list[SimpleNamespace]:
    """One non-overlapping call a day: 70/30 leans landing exactly half the time."""
    rows: list[SimpleNamespace] = []
    for i in range(days):
        p = "0.7000" if i % 2 == 0 else "0.3000"
        rows.append(_row(_PROMOTED + timedelta(days=i), p, 1 if i % 4 in (0, 1) else 0))
    return rows


# ---- attribution -------------------------------------------------------------


def test_only_the_champions_own_resolved_calls_count() -> None:
    """Baseline-rule calls share the lane in production, and calls from
    before the promotion were made by a predecessor — neither is evidence
    about this champion's confidence."""
    rows = [
        _row(_PROMOTED - timedelta(days=2), "0.7000", 1),  # predecessor
        _row(_PROMOTED, "0.6000", 1),
        _row(_PROMOTED + timedelta(days=1), "0.5500", 0, model="baseline_rule(h=24)"),
        _row(_PROMOTED + timedelta(days=2), "0.4000", 0),
        _row(_PROMOTED + timedelta(days=3), "0.6500", None),  # not resolved yet
    ]
    calls = champion_live_calls(rows, promoted_at=_PROMOTED)  # type: ignore[arg-type]
    assert calls == [(0.6, 1), (0.4, 0)]  # oldest first


def test_the_models_own_probability_is_used_so_corrections_never_stack() -> None:
    rows = [_row(_PROMOTED, "0.5600", 1, p_up_model="0.7000")]
    assert champion_live_calls(rows, promoted_at=_PROMOTED) == [(0.7, 1)]  # type: ignore[arg-type]


def test_overlapping_hourly_calls_collapse_to_independent_days() -> None:
    hourly = [
        _row(_PROMOTED + timedelta(hours=h), "0.6000", 1) for h in range(0, 24 * 3)
    ]
    calls = champion_live_calls(hourly, promoted_at=_PROMOTED)  # type: ignore[arg-type]
    # 72 hourly calls on a 24-hour horizon cover three days of market time.
    assert 2 <= len(calls) <= 3


def test_promoted_at_must_be_a_timezone_aware_timestamp() -> None:
    assert parse_promoted_at({"promoted_at": _PROMOTED.isoformat()}) == _PROMOTED
    assert parse_promoted_at({"promoted_at": "2026-10-06T12:00:00"}) is None
    assert parse_promoted_at({"promoted_at": "not a date"}) is None
    assert parse_promoted_at(None) is None


# ---- the store ---------------------------------------------------------------


def _applied(slope: float) -> LiveRecalibration:
    return LiveRecalibration(
        applied=True,
        slope=slope,
        n_independent=40,
        required=30,
        n_fit=20,
        n_holdout=20,
        brier_before=0.29,
        brier_after=0.25,
        reason="applied",
    )


def test_a_correction_applies_only_to_the_model_it_was_learned_from(tmp_path: Path) -> None:
    store = LiveCalibrationStore(tmp_path)
    assert store.active_slope_for("auto_a") == 1.0  # nothing decided yet
    store.write(model_name="auto_a", decided_at=_PROMOTED, result=_applied(0.4))
    assert store.active_slope_for("auto_a") == 0.4
    assert store.active_slope_for("auto_b") == 1.0  # a new champion starts clean


def test_a_decision_that_was_not_applied_changes_nothing(tmp_path: Path) -> None:
    store = LiveCalibrationStore(tmp_path)
    refused = LiveRecalibration(applied=False, slope=0.4, n_independent=40, required=30)
    store.write(model_name="auto_a", decided_at=_PROMOTED, result=refused)
    assert store.active_slope_for("auto_a") == 1.0
    data = store.read()
    assert data is not None and data["slope"] == 0.4  # still audited


def test_a_torn_file_degrades_to_no_correction(tmp_path: Path) -> None:
    (tmp_path / "live_calibration.json").write_text('{"model_name": "auto_a", "app', "utf-8")
    assert LiveCalibrationStore(tmp_path).active_slope_for("auto_a") == 1.0


# ---- the retrain hook --------------------------------------------------------


class _FakePredictions:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self.rows = rows
        self.since_calls: list[tuple[str, datetime]] = []

    async def list_resolved_since(self, *, timeframe: str, since: datetime) -> list[Any]:
        self.since_calls.append((timeframe, since))
        return [r for r in self.rows if r.asof >= since]

    async def list_resolved(self, limit: int = 1000, **_: Any) -> list[Any]:
        return [r for r in self.rows if r.realised_outcome is not None][:limit]


def _write_champion(tmp_path: Path, *, promoted_at: str | None) -> None:
    payload: dict[str, object] = {"model_name": "auto_a", "test_brier": 0.245}
    if promoted_at is not None:
        payload["promoted_at"] = promoted_at
    (tmp_path / "champion.json").write_text(json.dumps(payload), "utf-8")


async def test_a_kept_champion_is_recalibrated_and_the_lesson_records_it(
    tmp_path: Path,
) -> None:
    _write_champion(tmp_path, promoted_at=_PROMOTED.isoformat())
    preds = _FakePredictions(_daily_overconfident(40))
    service = PromotionService(model_store_dir=tmp_path, predictions=preds)  # type: ignore[arg-type]

    recal = await service._refresh_live_calibration(Timeframe.H1)
    assert recal is not None and recal["applied"] is True
    assert preds.since_calls == [("1h", _PROMOTED)]
    assert LiveCalibrationStore(tmp_path).active_slope_for("auto_a") < 1.0

    result = SimpleNamespace(
        promoted=False,
        demoted=False,
        challenger_family="technical",
        challenger_brier=0.249,
        champion_brier_fresh=0.246,
    )
    challenger = SimpleNamespace(report=SimpleNamespace(feature_importances={"ret_5": 0.01}))
    await service._log_lesson(result, challenger, {"technical": 0.25}, recal)  # type: ignore[arg-type]

    lesson = service.lessons_history(limit=1)[0]
    assert lesson["live_recalibration"] == recal
    buckets = lesson["calibration_buckets"]
    assert isinstance(buckets, list) and buckets
    assert {"bucket", "stated_midpoint", "realised_hit_rate", "samples"} <= set(buckets[0])
    # Feature selection still reads training-time importances only.
    assert lesson["importances"] == {"ret_5": 0.01}


async def test_a_new_champion_starts_on_its_own_calibration(tmp_path: Path) -> None:
    # Promoted after every recorded call — none of them are its own.
    _write_champion(tmp_path, promoted_at=(_PROMOTED + timedelta(days=60)).isoformat())
    service = PromotionService(
        model_store_dir=tmp_path,
        predictions=_FakePredictions(_daily_overconfident(40)),  # type: ignore[arg-type]
    )
    recal = await service._refresh_live_calibration(Timeframe.H1)
    assert recal is not None
    assert recal["applied"] is False and recal["n_independent"] == 0


async def test_no_champion_means_no_correction(tmp_path: Path) -> None:
    LiveCalibrationStore(tmp_path).write(
        model_name="auto_old", decided_at=_PROMOTED, result=_applied(0.4)
    )
    service = PromotionService(
        model_store_dir=tmp_path,
        predictions=_FakePredictions([]),  # type: ignore[arg-type]
    )
    assert await service._refresh_live_calibration(Timeframe.H1) is None
    assert LiveCalibrationStore(tmp_path).read() is None


async def test_a_champion_without_a_promotion_time_is_never_fitted(tmp_path: Path) -> None:
    _write_champion(tmp_path, promoted_at=None)
    service = PromotionService(
        model_store_dir=tmp_path,
        predictions=_FakePredictions(_daily_overconfident(40)),  # type: ignore[arg-type]
    )
    assert await service._refresh_live_calibration(Timeframe.H1) is None
    assert LiveCalibrationStore(tmp_path).active_slope_for("auto_a") == 1.0


# ---- inference ---------------------------------------------------------------


class _FixedForecaster:
    """Says 70% up every time."""

    name = "sklearn_hgb(h=24)"
    horizon_bars = 24

    def forecast(self, *, bars: Any, symbol: str, timeframe: Timeframe, **_: Any) -> Forecast:
        return Forecast(
            symbol=symbol,
            timeframe=timeframe,
            asof=bars[-1].ts,
            asof_close=Decimal(bars[-1].close),
            horizon_bars=24,
            p_up=Decimal("0.7000"),
            confidence=Decimal("0.4000"),
            direction=Direction.LONG,
            model_name=self.name,
            reasoning="ML lean.",
            features={},
        )


class _OneBarPrices:
    async def range(self, **_: Any) -> list[Any]:
        return [
            SimpleNamespace(
                symbol="EURUSD",
                timeframe="1h",
                ts=_PROMOTED,
                open="1.1",
                high="1.1",
                low="1.1",
                close="1.1",
                volume=None,
                source="test",
            )
        ]


class _CapturingPredictions:
    def __init__(self) -> None:
        self.recorded: list[Forecast] = []

    async def record(self, forecast: Forecast) -> Any:
        self.recorded.append(forecast)
        return "id"


def _service(tmp_path: Path, preds: _CapturingPredictions) -> ForecastService:
    service = ForecastService(
        prices=_OneBarPrices(),  # type: ignore[arg-type]
        predictions=preds,  # type: ignore[arg-type]
        model_store_dir=tmp_path,
    )
    service._resolve_forecaster = lambda *a, **k: _FixedForecaster()  # type: ignore[method-assign,assignment,return-value]
    return service


@pytest.mark.parametrize("model_name, expect_corrected", [("auto_a", True), ("auto_b", False)])
async def test_inference_applies_the_correction_only_to_its_champion(
    tmp_path: Path, model_name: str, expect_corrected: bool
) -> None:
    LiveCalibrationStore(tmp_path).write(
        model_name="auto_a", decided_at=_PROMOTED, result=_applied(0.5)
    )
    preds = _CapturingPredictions()
    payload = await _service(tmp_path, preds).predict(
        symbol="EURUSD", timeframe=Timeframe.H1, model_name=model_name
    )
    recorded = preds.recorded[0]
    if expect_corrected:
        assert payload.forecast.p_up == Decimal(str(round(recalibrate(0.7, 0.5), 4)))
        # What the model itself said is recorded beside the restated number.
        assert recorded.p_up_model == Decimal("0.7000")
    else:
        assert payload.forecast.p_up == Decimal("0.7000")
        assert recorded.p_up_model is None
