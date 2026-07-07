"""Forecasting endpoints — Phase 4."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from mentor.api.deps import SessionDep, SettingsDep
from mentor.application.forecasting import (
    ForecastService,
    TrainingService,
    resolve_pending_predictions,
)
from mentor.application.forecasting.postmortem import compute_post_mortem
from mentor.application.forecasting.promotion import PromotionService
from mentor.application.forecasting.replay import ReplayService
from mentor.application.forecasting.vol_service import VolService
from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.forecast import Direction
from mentor.domain.forecasting.volatility import (
    VolForecast,
    VolRegime,
    build_sizing_guidance,
)
from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.forecasting.model_store import ModelStore
from mentor.infrastructure.forecasting.sklearn_forecaster import TrainingReport
from mentor.infrastructure.repositories import (
    PredictionRepository,
    PriceBarRepository,
)
from mentor.infrastructure.repositories.macro_series import MacroSeriesRepository
from mentor.infrastructure.repositories.news_tone import NewsToneRepository

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
        news_tone=NewsToneRepository(session),
        news_query_key=settings.news_query_key,
        macro=MacroSeriesRepository(session),
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
    include_news: bool = False
    include_macro: bool = False


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
    ece: float = 0.0
    ece_uncalibrated: float = 0.0
    test_brier_uncalibrated: float = 0.0
    calibration_applied: bool = False
    n_calibration: int = 0


@router.post("/train", response_model=TrainReport)
async def train(body: TrainRequest, session: SessionDep, settings: SettingsDep) -> TrainReport:
    service = TrainingService(
        PriceBarRepository(session),
        settings.model_store_dir,
        news_tone=NewsToneRepository(session),
        news_query_key=settings.news_query_key,
        macro=MacroSeriesRepository(session),
    )
    try:
        forecaster, meta = await service.train(
            symbol=body.symbol,
            timeframe=body.timeframe,
            start=body.start,
            end=body.end,
            horizon_bars=body.horizon_bars,
            model_name=body.model_name,
            include_news=body.include_news,
            include_macro=body.include_macro,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _train_report_dto(meta.name, forecaster.report)


def _train_report_dto(name: str, r: TrainingReport) -> TrainReport:
    return TrainReport(
        name=name,
        horizon_bars=r.horizon_bars,
        n_samples=r.n_samples,
        n_train=r.n_train,
        n_test=r.n_test,
        train_accuracy=r.train_accuracy,
        test_accuracy=r.test_accuracy,
        test_log_loss=r.test_log_loss,
        test_brier=r.test_brier,
        feature_importances=r.feature_importances,
        ece=r.ece,
        ece_uncalibrated=r.ece_uncalibrated,
        test_brier_uncalibrated=r.test_brier_uncalibrated,
        calibration_applied=r.calibration_applied,
        n_calibration=r.n_calibration,
    )


@router.get("/models", response_model=list[TrainReport])
async def list_models(settings: SettingsDep) -> list[TrainReport]:
    store = ModelStore(settings.model_store_dir)
    return [_train_report_dto(meta.name, meta.report) for meta in store.list()]


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
    correct: bool | None  # hit/miss for directional calls; null for neutral or pending
    features: dict[str, Decimal]


def _directional_hit(direction: str, outcome: int | None) -> bool | None:
    if outcome is None:
        return None
    if direction == Direction.LONG.value:
        return outcome == 1
    if direction == Direction.SHORT.value:
        return outcome == 0
    return None  # neutral — no directional stance


@router.get("/audit", response_model=list[AuditPredictionDTO])
async def audit_log(session: SessionDep, limit: int = 100) -> list[AuditPredictionDTO]:
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
            correct=_directional_hit(row.direction, row.realised_outcome),
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


# ---------- volatility (predict the range, not the arrow) ----------


class VolForecastDTO(BaseModel):
    symbol: str
    timeframe: Timeframe
    asof: datetime
    asof_close: Decimal
    horizon_bars: int
    expected_vol: Decimal
    expected_range_pips: Decimal
    percentile_vs_history: Decimal
    regime: VolRegime
    model_name: str
    reasoning: str
    range_low_pips: Decimal | None = None
    range_high_pips: Decimal | None = None
    coverage: Decimal | None = None


class VolEvalDTO(BaseModel):
    n_test: int
    ml_mae: float
    ewma_mae: float
    ml_qlike: float
    ewma_qlike: float
    ml_r2: float
    r2_vs_ewma: float
    beats_ewma: bool
    verdict: str
    feature_importances: dict[str, float]


class VolGuidanceDTO(BaseModel):
    suggested_stop_pips: Decimal
    event_freeze: bool
    rationale: str


class VolResponse(BaseModel):
    forecast: VolForecastDTO  # headline read (EWMA, or ML if it wins out-of-sample)
    baseline: VolForecastDTO  # always the transparent EWMA read
    guidance: VolGuidanceDTO  # stop-distance suggestion + event-freeze flag
    eval: VolEvalDTO | None  # present only when the ML model was trained + graded


class VolRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"symbol": "EURUSD", "timeframe": "1d", "horizon_bars": 5, "model": "ewma"}
        }
    )

    symbol: str = "EURUSD"
    timeframe: Timeframe = Timeframe.D1
    horizon_bars: Annotated[int, Field(ge=1, le=60)] = 5
    model: str = "ewma"  # "ewma" (baseline) or "ml" (train + grade vs EWMA)


def _vol_dto(f: VolForecast) -> VolForecastDTO:
    return VolForecastDTO(
        symbol=f.symbol,
        timeframe=f.timeframe,
        asof=f.asof,
        asof_close=f.asof_close,
        horizon_bars=f.horizon_bars,
        expected_vol=f.expected_vol,
        expected_range_pips=f.expected_range_pips,
        percentile_vs_history=f.percentile_vs_history,
        regime=f.regime,
        model_name=f.model_name,
        reasoning=f.reasoning,
        range_low_pips=f.range_low_pips,
        range_high_pips=f.range_high_pips,
        coverage=f.coverage,
    )


@router.post("/volatility", response_model=VolResponse)
async def volatility(body: VolRequest, session: SessionDep) -> VolResponse:
    """Expected *range* over the next H bars — the one honestly-forecastable
    target. EWMA baseline always; ``model='ml'`` also trains a regressor and
    only makes it the headline if it beats EWMA out-of-sample."""
    service = VolService(
        prices=PriceBarRepository(session), macro=MacroSeriesRepository(session)
    )
    try:
        payload = await service.predict_vol(
            symbol=body.symbol,
            timeframe=body.timeframe,
            horizon_bars=body.horizon_bars,
            model=body.model,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ev: VolEvalDTO | None = None
    if payload.eval is not None:
        r = payload.eval
        ev = VolEvalDTO(
            n_test=r.n_test,
            ml_mae=r.ml_mae,
            ewma_mae=r.ewma_mae,
            ml_qlike=r.ml_qlike,
            ewma_qlike=r.ewma_qlike,
            ml_r2=r.ml_r2,
            r2_vs_ewma=r.r2_vs_ewma,
            beats_ewma=r.beats_ewma,
            verdict=r.verdict,
            feature_importances=r.feature_importances,
        )
    guidance = build_sizing_guidance(payload.forecast)
    return VolResponse(
        forecast=_vol_dto(payload.forecast),
        baseline=_vol_dto(payload.baseline),
        guidance=VolGuidanceDTO(
            suggested_stop_pips=guidance.suggested_stop_pips,
            event_freeze=guidance.event_freeze,
            rationale=guidance.rationale,
        ),
        eval=ev,
    )


# ---------- autonomous loop: replay, run-once, status, post-mortem ----------


class ReplayRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "EURUSD",
                "timeframe": "1h",
                "model_name": "baseline",
                "horizon_bars": 24,
                "max_points": 200,
            }
        }
    )

    symbol: str = "EURUSD"
    timeframe: Timeframe = Timeframe.H1
    model_name: str = "baseline"
    horizon_bars: Annotated[int, Field(ge=1, le=240)] = 24
    max_points: Annotated[int, Field(ge=1, le=2000)] = 200
    stride: Annotated[int, Field(ge=1, le=24)] = 1


class ReplayResponse(BaseModel):
    symbol: str
    timeframe: Timeframe
    model_name: str
    points_evaluated: int
    predictions_written: int
    skipped_existing: int


@router.post("/replay", response_model=ReplayResponse)
async def replay(body: ReplayRequest, session: SessionDep, settings: SettingsDep) -> ReplayResponse:
    """Backfill the audit log with point-in-time historical predictions that
    resolve immediately against bars that have already printed — so the
    System Predictions view and the post-mortem have real hits/misses now."""
    service = ReplayService(
        prices=PriceBarRepository(session),
        predictions=PredictionRepository(session),
        model_store_dir=settings.model_store_dir,
        news_tone=NewsToneRepository(session),
        news_query_key=settings.news_query_key,
        macro=MacroSeriesRepository(session),
    )
    try:
        result = await service.replay(
            symbol=body.symbol,
            timeframe=body.timeframe,
            model_name=body.model_name,
            horizon_bars=body.horizon_bars,
            max_points=body.max_points,
            stride=body.stride,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReplayResponse(
        symbol=result.symbol,
        timeframe=Timeframe(result.timeframe),
        model_name=result.model_name,
        points_evaluated=result.points_evaluated,
        predictions_written=result.predictions_written,
        skipped_existing=result.skipped_existing,
    )


class CycleResponse(BaseModel):
    predicted: bool
    prediction_id: str | None
    resolved: int
    note: str


@router.post("/loop/run-once", response_model=CycleResponse)
async def loop_run_once(request: Request) -> CycleResponse:
    """Fire one predict + resolve cycle immediately (for testing without
    waiting for the scheduler's next tick)."""
    scheduler = request.app.state.scheduler
    result = await scheduler.run_cycle_once()
    return CycleResponse(
        predicted=result.predicted,
        prediction_id=result.prediction_id,
        resolved=result.resolved,
        note=result.note,
    )


class RetrainResponse(BaseModel):
    result: str


@router.post("/loop/retrain", response_model=RetrainResponse)
async def loop_retrain(request: Request) -> RetrainResponse:
    """Retrain a challenger and promote it only if it beats the champion."""
    scheduler = request.app.state.scheduler
    reason = await scheduler.run_retrain_once()
    return RetrainResponse(result=reason)


class LoopJobDTO(BaseModel):
    id: str
    next_run: str | None


class LoopStatusResponse(BaseModel):
    enabled: bool
    running: bool
    symbol: str
    timeframe: str
    horizon_bars: int
    champion: str
    jobs: list[LoopJobDTO]


@router.get("/loop/status", response_model=LoopStatusResponse)
async def loop_status(request: Request) -> LoopStatusResponse:
    scheduler = request.app.state.scheduler
    return LoopStatusResponse(**scheduler.status())


class FeatureContrastDTO(BaseModel):
    feature: str
    mean_on_hits: float
    mean_on_misses: float
    gap: float


class PostMortemCalibrationDTO(BaseModel):
    bucket: str
    stated_midpoint: float
    realised_hit_rate: float
    samples: int


class PostMortemResponse(BaseModel):
    sample_size: int
    directional: int
    neutral: int
    hits: int
    misses: int
    directional_accuracy: float
    avg_confidence_on_hits: float
    avg_confidence_on_misses: float
    brier_score: float
    ece: float
    headline: str
    feature_contrasts: list[FeatureContrastDTO]
    calibration: list[PostMortemCalibrationDTO]


@router.get("/postmortem", response_model=PostMortemResponse)
async def postmortem(session: SessionDep) -> PostMortemResponse:
    """Why the system's predictions hit or missed — calibration + feature
    attribution over all resolved predictions. Honest by design: it finds
    where the model is overconfident, not a market-beating signal."""
    rows = await PredictionRepository(session).list_resolved()
    pm = compute_post_mortem(rows)
    return PostMortemResponse(
        sample_size=pm.sample_size,
        directional=pm.directional,
        neutral=pm.neutral,
        hits=pm.hits,
        misses=pm.misses,
        directional_accuracy=pm.directional_accuracy,
        avg_confidence_on_hits=pm.avg_confidence_on_hits,
        avg_confidence_on_misses=pm.avg_confidence_on_misses,
        brier_score=pm.brier_score,
        ece=pm.ece,
        headline=pm.headline,
        feature_contrasts=[
            FeatureContrastDTO(
                feature=c.feature,
                mean_on_hits=c.mean_on_hits,
                mean_on_misses=c.mean_on_misses,
                gap=c.gap,
            )
            for c in pm.feature_contrasts
        ],
        calibration=[
            PostMortemCalibrationDTO(
                bucket=b.bucket,
                stated_midpoint=b.stated_midpoint,
                realised_hit_rate=b.realised_hit_rate,
                samples=b.samples,
            )
            for b in pm.calibration
        ],
    )


class ChampionResponse(BaseModel):
    champion: dict[str, object] | None


@router.get("/champion", response_model=ChampionResponse)
async def champion(settings: SettingsDep) -> ChampionResponse:
    promo = PromotionService(model_store_dir=settings.model_store_dir)
    return ChampionResponse(champion=promo.current_champion())
