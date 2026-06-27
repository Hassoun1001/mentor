"""Inference orchestrator.

Picks the forecaster (baseline or a named ML model), runs it against
the latest visible bars, records the prediction in the audit log, and
returns the forecast.

The audit-log write happens *before* the API returns — so every
prediction the UI sees is queryable later for calibration.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting import Forecast
from mentor.domain.forecasting.baseline import BaselineForecaster
from mentor.domain.forecasting.forecaster import Forecaster
from mentor.domain.forecasting.regime import RegimeAdjustedForecaster
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.forecasting.model_store import ModelStore
from mentor.infrastructure.forecasting.sklearn_forecaster import SklearnForecaster
from mentor.infrastructure.repositories.predictions import PredictionRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository


def _to_domain(rows) -> list[PriceBar]:  # type: ignore[no-untyped-def]
    return [
        PriceBar(
            symbol=r.symbol,
            timeframe=Timeframe(r.timeframe),
            ts=r.ts,
            open=Decimal(r.open),
            high=Decimal(r.high),
            low=Decimal(r.low),
            close=Decimal(r.close),
            volume=Decimal(r.volume) if r.volume is not None else None,
            source=r.source,
        )
        for r in rows
    ]


@dataclass(frozen=True, slots=True)
class ForecastPayload:
    forecast: Forecast
    prediction_id: uuid.UUID


class ForecastService:
    def __init__(
        self,
        *,
        prices: PriceBarRepository,
        predictions: PredictionRepository,
        model_store_dir: str | Path,
    ) -> None:
        self._prices = prices
        self._predictions = predictions
        self._store = ModelStore(model_store_dir)

    async def predict(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        model_name: str = "baseline",
        horizon_bars: int = 24,
        history_bars: int = 600,
        record: bool = True,
        regime_aware: bool = True,
    ) -> ForecastPayload:
        end = datetime.now(UTC)
        start = end - timedelta(seconds=history_bars * timeframe.seconds * 2)
        rows = await self._prices.range(symbol=symbol, timeframe=timeframe, start=start, end=end)
        if not rows:
            raise ValidationError(f"no bars for {symbol} {timeframe.value} — backfill first")
        bars = _to_domain(rows)

        forecaster = self._resolve_forecaster(model_name, horizon_bars, regime_aware=regime_aware)
        forecast = forecaster.forecast(bars=bars, symbol=symbol, timeframe=timeframe)

        prediction_id = uuid.uuid4()
        if record:
            prediction_id = await self._predictions.record(forecast)

        return ForecastPayload(forecast=forecast, prediction_id=prediction_id)

    def _resolve_forecaster(
        self, model_name: str, horizon_bars: int, *, regime_aware: bool
    ) -> Forecaster:
        if model_name == "baseline":
            # The baseline rule model has no empirical training distribution,
            # so regime-wrapping it would scale by 0. We leave it unwrapped.
            return BaselineForecaster(horizon_bars=horizon_bars)
        forecaster, _meta = self._store.load(model_name)
        if (
            regime_aware
            and isinstance(forecaster, SklearnForecaster)
            and forecaster.distribution is not None
        ):
            return RegimeAdjustedForecaster(base=forecaster, distribution=forecaster.distribution)
        return forecaster
