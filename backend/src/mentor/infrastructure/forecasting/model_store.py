"""Trained-model persistence.

Stored under `models/` next to the running process. The store keeps a
metadata sidecar so we can list models without unpickling — auditing
which model produced which prediction is half the calibration loop.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib

from mentor.domain.errors import ValidationError
from mentor.infrastructure.forecasting.sklearn_forecaster import (
    SklearnForecaster,
    TrainingReport,
)


@dataclass(frozen=True, slots=True)
class StoredModelMeta:
    name: str
    horizon_bars: int
    trained_at: datetime
    train_start: datetime | None
    train_end: datetime | None
    symbol: str
    timeframe: str
    report: TrainingReport


class ModelStore:
    def __init__(self, directory: str | Path) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        forecaster: SklearnForecaster,
        *,
        name: str,
        symbol: str,
        timeframe: str,
        train_start: datetime | None = None,
        train_end: datetime | None = None,
    ) -> StoredModelMeta:
        if not name.replace("-", "").replace("_", "").isalnum():
            raise ValidationError("model name must be alphanumeric (plus - or _)", field="name")
        artifact_path = self._dir / f"{name}.joblib"
        meta_path = self._dir / f"{name}.json"

        joblib.dump(forecaster, artifact_path)

        meta = StoredModelMeta(
            name=name,
            horizon_bars=forecaster.horizon_bars,
            trained_at=datetime.now(UTC),
            train_start=train_start,
            train_end=train_end,
            symbol=symbol.upper(),
            timeframe=timeframe,
            report=forecaster.report,
        )
        meta_path.write_text(
            json.dumps(_meta_to_dict(meta), default=str, indent=2),
            encoding="utf-8",
        )
        return meta

    def load(self, name: str) -> tuple[SklearnForecaster, StoredModelMeta]:
        artifact_path = self._dir / f"{name}.joblib"
        meta_path = self._dir / f"{name}.json"
        if not artifact_path.exists() or not meta_path.exists():
            raise ValidationError(f"model {name!r} not found", field="name")
        forecaster: SklearnForecaster = joblib.load(artifact_path)
        meta = _dict_to_meta(json.loads(meta_path.read_text(encoding="utf-8")))
        return forecaster, meta

    def list(self) -> Iterator[StoredModelMeta]:
        for meta_path in sorted(self._dir.glob("*.json")):
            # Only sidecars that have a matching artifact are model metadata.
            # This skips bookkeeping files that also live here — champion.json,
            # and anything else without a companion .joblib — which would
            # otherwise blow up `_dict_to_meta` (no 'report' key).
            if not meta_path.with_suffix(".joblib").exists():
                continue
            try:
                payload = json.loads(meta_path.read_text(encoding="utf-8"))
                yield _dict_to_meta(payload)
            except (ValueError, KeyError, TypeError):
                # A malformed or legacy sidecar must not break the listing.
                continue


def _meta_to_dict(meta: StoredModelMeta) -> dict[str, object]:
    d = dataclasses.asdict(meta)
    # asdict turns TrainingReport into a dict already — fine
    return d


def _dict_to_meta(payload: dict[str, Any]) -> StoredModelMeta:
    report_payload = payload["report"]
    report = TrainingReport(
        n_samples=int(report_payload["n_samples"]),
        n_train=int(report_payload["n_train"]),
        n_test=int(report_payload["n_test"]),
        train_accuracy=float(report_payload["train_accuracy"]),
        test_accuracy=float(report_payload["test_accuracy"]),
        test_log_loss=float(report_payload["test_log_loss"]),
        test_brier=float(report_payload["test_brier"]),
        horizon_bars=int(report_payload["horizon_bars"]),
        feature_importances={
            k: float(v) for k, v in report_payload.get("feature_importances", {}).items()
        },
        n_calibration=int(report_payload.get("n_calibration", 0)),
        test_brier_uncalibrated=float(report_payload.get("test_brier_uncalibrated", 0.0)),
        ece=float(report_payload.get("ece", 0.0)),
        ece_uncalibrated=float(report_payload.get("ece_uncalibrated", 0.0)),
        calibration_applied=bool(report_payload.get("calibration_applied", False)),
        # Abstention policy. `.get` with defaults so sidecars written before
        # selective prediction existed still load as never-abstaining models —
        # but they MUST be read, or every model reads back with a zeroed
        # policy and the gate silently compares all-hours Brier instead.
        abstain_margin=float(report_payload.get("abstain_margin", 0.0)),
        coverage=float(report_payload.get("coverage", 1.0)),
        n_covered=int(report_payload.get("n_covered", 0)),
        test_brier_covered=float(report_payload.get("test_brier_covered", 0.0)),
        test_accuracy_covered=float(report_payload.get("test_accuracy_covered", 0.0)),
    )
    return StoredModelMeta(
        name=payload["name"],
        horizon_bars=int(payload["horizon_bars"]),
        trained_at=_parse_dt(payload["trained_at"]),
        train_start=_parse_dt(payload["train_start"]) if payload.get("train_start") else None,
        train_end=_parse_dt(payload["train_end"]) if payload.get("train_end") else None,
        symbol=payload["symbol"],
        timeframe=payload["timeframe"],
        report=report,
    )


def _parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt
