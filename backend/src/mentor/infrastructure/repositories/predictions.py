"""Prediction audit-log persistence."""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.domain.forecasting.forecast import Forecast
from mentor.infrastructure.models import PredictionORM


class PredictionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, forecast: Forecast) -> uuid.UUID:
        horizon_at = forecast.asof + timedelta(
            seconds=forecast.horizon_bars * forecast.timeframe.seconds
        )
        prediction_id = uuid.uuid4()
        self._session.add(
            PredictionORM(
                id=prediction_id,
                symbol=forecast.symbol,
                timeframe=forecast.timeframe.value,
                asof=forecast.asof,
                asof_close=forecast.asof_close,
                horizon_bars=forecast.horizon_bars,
                horizon_at=horizon_at,
                model_name=forecast.model_name,
                p_up=forecast.p_up,
                confidence=forecast.confidence,
                direction=forecast.direction.value,
                reasoning=forecast.reasoning,
                features_json=json.dumps({k: str(v) for k, v in forecast.features.items()}),
            )
        )
        await self._session.flush()
        return prediction_id

    async def record_and_resolve(
        self, forecast: Forecast, *, realised_close: Decimal, resolved_at: datetime
    ) -> uuid.UUID:
        """Log a prediction whose outcome is already known (replay path).

        Used to backfill the audit log from history: predict at a past
        point, then immediately resolve against the bar that has since
        printed. No lookahead — the caller supplies a forecast built only
        from data up to `forecast.asof` and the close `horizon_bars` later.
        """
        prediction_id = await self.record(forecast)
        await self.resolve(prediction_id, realised_close=realised_close, resolved_at=resolved_at)
        return prediction_id

    async def list_recent(self, limit: int = 50) -> Sequence[PredictionORM]:
        stmt = select(PredictionORM).order_by(PredictionORM.asof.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_resolved(self, limit: int = 1000) -> Sequence[PredictionORM]:
        stmt = (
            select(PredictionORM)
            .where(PredictionORM.resolved_at.is_not(None))
            .order_by(PredictionORM.asof.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def exists_at(
        self, *, symbol: str, timeframe: str, asof: datetime, model_name: str
    ) -> bool:
        """True if a prediction for this exact (symbol, timeframe, asof, model)
        already exists — lets replay/scheduling be idempotent."""
        stmt = (
            select(PredictionORM.id)
            .where(
                and_(
                    PredictionORM.symbol == symbol.upper(),
                    PredictionORM.timeframe == timeframe,
                    PredictionORM.asof == asof,
                    PredictionORM.model_name == model_name,
                )
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.first() is not None

    async def unresolved_due_by(self, before: datetime) -> Sequence[PredictionORM]:
        stmt = select(PredictionORM).where(
            and_(
                PredictionORM.resolved_at.is_(None),
                PredictionORM.horizon_at <= before,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def resolve(
        self,
        prediction_id: uuid.UUID,
        *,
        realised_close: Decimal,
        resolved_at: datetime,
    ) -> None:
        orm = await self._session.get(PredictionORM, prediction_id)
        if orm is None:
            return
        orm.realised_close = realised_close
        orm.realised_outcome = 1 if realised_close > orm.asof_close else 0
        orm.resolved_at = resolved_at
        await self._session.flush()

    async def calibration_summary(self) -> dict[str, dict[str, float]]:
        """Group resolved predictions by 10% probability bucket and
        return realised hit rate per bucket. This is the actual
        calibration loop the plan calls out (§6.D Confidence + calibration).
        """
        stmt = select(PredictionORM).where(PredictionORM.resolved_at.is_not(None))
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        buckets: dict[str, list[int]] = {}
        for row in rows:
            bucket_low = int(float(row.p_up) * 10) * 10
            label = f"{bucket_low}-{bucket_low + 10}%"
            buckets.setdefault(label, []).append(int(row.realised_outcome or 0))
        return {
            label: {
                "samples": float(len(values)),
                "hit_rate": float(sum(values) / len(values)) if values else 0.0,
            }
            for label, values in sorted(buckets.items())
        }
