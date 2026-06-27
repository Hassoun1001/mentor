"""Alerts persistence."""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.domain.alerts.alert import (
    Alert,
    AlertCondition,
    AlertKind,
    AlertStatus,
)
from mentor.infrastructure.models import AlertORM


def _condition_to_json(c: AlertCondition) -> str:
    return json.dumps(
        {
            "symbol": c.symbol,
            "price_level": str(c.price_level) if c.price_level is not None else None,
            "model_name": c.model_name,
            "target_direction": c.target_direction,
            "category_min_impact": (
                str(c.category_min_impact) if c.category_min_impact is not None else None
            ),
            "freeze_minutes_before": c.freeze_minutes_before,
            "freeze_minutes_after": c.freeze_minutes_after,
        }
    )


def _condition_from_json(blob: str) -> AlertCondition:
    payload = json.loads(blob)
    return AlertCondition(
        symbol=payload.get("symbol"),
        price_level=(Decimal(payload["price_level"]) if payload.get("price_level") else None),
        model_name=payload.get("model_name"),
        target_direction=payload.get("target_direction"),
        category_min_impact=(
            Decimal(payload["category_min_impact"]) if payload.get("category_min_impact") else None
        ),
        freeze_minutes_before=int(payload.get("freeze_minutes_before", 30)),
        freeze_minutes_after=int(payload.get("freeze_minutes_after", 30)),
    )


def _from_orm(orm: AlertORM) -> Alert:
    return Alert(
        id=orm.id,
        kind=AlertKind(orm.kind),
        label=orm.label,
        status=AlertStatus(orm.status),
        condition=_condition_from_json(orm.condition_json),
        created_at=orm.created_at,
        fired_at=orm.fired_at,
        last_evaluated_at=orm.last_evaluated_at,
    )


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, alert: Alert) -> Alert:
        orm = AlertORM(
            id=alert.id,
            kind=alert.kind.value,
            label=alert.label,
            status=alert.status.value,
            condition_json=_condition_to_json(alert.condition),
            fired_at=alert.fired_at,
            last_evaluated_at=alert.last_evaluated_at,
        )
        self._session.add(orm)
        await self._session.flush()
        return _from_orm(orm)

    async def get(self, alert_id: uuid.UUID) -> Alert | None:
        orm = await self._session.get(AlertORM, alert_id)
        return _from_orm(orm) if orm else None

    async def list_all(self) -> list[Alert]:
        result = await self._session.execute(select(AlertORM).order_by(AlertORM.created_at.desc()))
        return [_from_orm(o) for o in result.scalars().all()]

    async def list_armed(self) -> Sequence[AlertORM]:
        result = await self._session.execute(
            select(AlertORM).where(AlertORM.status == AlertStatus.ARMED.value)
        )
        return result.scalars().all()

    async def set_status(
        self,
        alert_id: uuid.UUID,
        status: AlertStatus,
        *,
        fired_at: datetime | None = None,
    ) -> Alert | None:
        orm = await self._session.get(AlertORM, alert_id)
        if orm is None:
            return None
        orm.status = status.value
        if status is AlertStatus.FIRED:
            orm.fired_at = fired_at or datetime.now(UTC)
        orm.last_evaluated_at = datetime.now(UTC)
        await self._session.flush()
        return _from_orm(orm)

    async def delete(self, alert_id: uuid.UUID) -> bool:
        orm = await self._session.get(AlertORM, alert_id)
        if orm is None:
            return False
        await self._session.delete(orm)
        await self._session.flush()
        return True
