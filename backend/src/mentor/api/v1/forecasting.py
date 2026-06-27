"""Forecasting endpoints — Phase 4."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from mentor.api.deps import SessionDep, SettingsDep
from mentor.application.forecasting import (
    ForecastService,
    TrainingService,
    resolve_pending_predictions,
)
from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.forecast import Direction
from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.forecasting.model_store import ModelStore
from mentor.infrastructure.repositories import (
    PredictionRepository,
    PriceBarRepository,
)

router = APIRouter(prefix="/forecasting", tags=["forecasting"])


# ---------- predict ----------


class PredictRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "EURUSD",
                "timeframe": "1h",
                "model_name": "baseline",
                "horizon_bars": 24,
            }
        }
    )

    symbol: str
    timeframe: Timeframe = Timeframe.H1
    model_name: str = "baseline"
    horizon_bars: Annotated[int, Field(ge=1, le=240)] = 24


class PredictResponse(BaseModel):
    prediction_id: uuid.UUID
    symbol: str
    timeframe: Timeframe
    asof: datetime
    asof_close: Decimal
    horizon_bars: int
    p_up: Decimal
    confidence: Decimal
    direction: Direction
    model_name: str
    reasoning: str
    features: dict[str, Decimal]


@router.post("/predict", response_model=PredictResponse)
async def predict(
    body: PredictRequest, session: SessionDep, settings: SettingsDep
) -> PredictResponse:
    service = ForecastService(
        prices=PriceBarRepository(session),
        predictions=PredictionRepository(session),
        model_store_dir=settings.model_store_dir,
    )
    try:
        payload = await service.predict(
            symbol=body.symbol,
            timeframe=body.timeframe,
            model_name=body.model_name,
            horizon_bars=body.horizon_bars,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    f = payload.forecast
    return PredictResponse(
        prediction_id=payload.prediction_id,
        symbol=f.symbol,
        timeframe=f.timeframe,
        asof=f.asof,
        asof_close=f.asof_close,
        horizon_bars=f.horizon_bars,
        p_up=f.p_up,
        confidence=f.confidence,
        direction=f.direction,
        model_name=f.model_name,
        reasoning=f.reasoning,
        features=f.features,
    )


# ---------- train ----------


class TrainRequest(BaseModel):
    symbol: str
    timeframe: Timeframe = Timeframe.H1
    start: datetime
    end: datetime
    horizon_bars: Annotated[int, Field(ge=1, le=240)] = 24
    model_name: str


class TrainReport(BaseModel):
    name: str
    horizon_bars: int
    n_samples: int
    n_train: int
    n_test: int
    train_accuracy: float
    test_accuracy: float
    test_log_loss: float
    test_brier: float
    feature_importances: dict[str, float]


@router.post("/train", response_model=TrainReport)
async def train(body: TrainRequest, session: SessionDep, settings: SettingsDep) -> TrainReport:
    service = TrainingService(PriceBarRepository(session), settings.model_store_dir)
    try:
        forecaster, meta = await service.train(
            symbol=body.symbol,
            timeframe=body.timeframe,
            start=body.start,
            end=body.end,
            horizon_bars=body.horizon_bars,
            model_name=body.model_name,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    r = forecaster.report
    return TrainReport(
        name=meta.name,
        horizon_bars=r.horizon_bars,
        n_samples=r.n_samples,
        n_train=r.n_train,
        n_test=r.n_test,
        train_accuracy=r.train_accuracy,
        test_accuracy=r.test_accuracy,
        test_log_loss=r.test_log_loss,
        test_brier=r.test_brier,
        feature_importances=r.feature_importances,
    )


@router.get("/models", response_model=list[TrainReport])
async def list_models(settings: SettingsDep) -> list[TrainReport]:
    store = ModelStore(settings.model_store_dir)
    out: list[TrainReport] = []
    for meta in store.list():
        r = meta.report
        out.append(
            TrainReport(
                name=meta.name,
                horizon_bars=r.horizon_bars,
                n_samples=r.n_samples,
                n_train=r.n_train,
                n_test=r.n_test,
                train_accuracy=r.train_accuracy,
                test_accuracy=r.test_accuracy,
                test_log_loss=r.test_log_loss,
                test_brier=r.test_brier,
                feature_importances=r.feature_importances,
            )
        )
    return out


# ---------- audit log + calibration ----------


class AuditPredictionDTO(BaseModel):
    id: uuid.UUID
    symbol: str
    timeframe: Timeframe
    asof: datetime
    horizon_at: datetime
    model_name: str
    p_up: Decimal
    confidence: Decimal
    direction: Direction
    reasoning: str
    asof_close: Decimal
    realised_close: Decimal | None
    realised_outcome: int | None
    features: dict[str, Decimal]


@router.get("/audit", response_model=list[AuditPredictionDTO])
async def audit_log(session: SessionDep, limit: int = 50) -> list[AuditPredictionDTO]:
    rows = await PredictionRepository(session).list_recent(limit=limit)
    return [
        AuditPredictionDTO(
            id=row.id,
            symbol=row.symbol,
            timeframe=Timeframe(row.timeframe),
            asof=row.asof,
            horizon_at=row.horizon_at,
            model_name=row.model_name,
            p_up=Decimal(row.p_up),
            confidence=Decimal(row.confidence),
            direction=Direction(row.direction),
            reasoning=row.reasoning,
            asof_close=Decimal(row.asof_close),
            realised_close=Decimal(row.realised_close) if row.realised_close is not None else None,
            realised_outcome=row.realised_outcome,
            features={k: Decimal(v) for k, v in json.loads(row.features_json).items()},
        )
        for row in rows
    ]


class ResolverResponse(BaseModel):
    examined: int
    resolved: int
    still_pending: int


@router.post("/audit/resolve", response_model=ResolverResponse)
async def resolve(session: SessionDep) -> ResolverResponse:
    result = await resolve_pending_predictions(
        predictions=PredictionRepository(session),
        prices=PriceBarRepository(session),
    )
    return ResolverResponse(
        examined=result.examined,
        resolved=result.resolved,
        still_pending=result.still_pending,
    )


class CalibrationBucket(BaseModel):
    bucket: str
    samples: float
    hit_rate: float


@router.get("/audit/calibration", response_model=list[CalibrationBucket])
async def calibration(session: SessionDep) -> list[CalibrationBucket]:
    summary = await PredictionRepository(session).calibration_summary()
    return [
        CalibrationBucket(bucket=label, samples=v["samples"], hit_rate=v["hit_rate"])
        for label, v in summary.items()
    ]


# ---------- helper for the front page ----------


class SnapshotRequest(BaseModel):
    symbol: str
    timeframe: Timeframe = Timeframe.H1
    model_name: str = "baseline"
    horizon_bars: Annotated[int, Field(ge=1, le=240)] = 24


class SnapshotResponse(BaseModel):
    forecast: PredictResponse
    horizon_at: datetime


@router.post("/snapshot", response_model=SnapshotResponse)
async def snapshot(
    body: SnapshotRequest, session: SessionDep, settings: SettingsDep
) -> SnapshotResponse:
    """Convenience wrapper: predict + return horizon ETA so the UI can
    show 'this read becomes truth at X' without recomputing."""
    fp = await predict(  # reuse the route handler directly
        PredictRequest(
            symbol=body.symbol,
            timeframe=body.timeframe,
            model_name=body.model_name,
            horizon_bars=body.horizon_bars,
        ),
        session,
        settings,
    )
    horizon_at = fp.asof + timedelta(seconds=fp.horizon_bars * fp.timeframe.seconds)
    return SnapshotResponse(forecast=fp, horizon_at=horizon_at)
