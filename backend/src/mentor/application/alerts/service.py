"""Alerts orchestrator — arm, sweep, fire."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from mentor.domain.alerts.alert import (
    Alert,
    AlertCondition,
    AlertKind,
    AlertStatus,
)
from mentor.domain.alerts.evaluation import evaluate_price_alert
from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.repositories.alerts import AlertRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.logging import get_logger

log = get_logger("mentor.alerts.service")


@dataclass(frozen=True, slots=True)
class SweepResult:
    evaluated: int
    fired: int


class AlertService:
    def __init__(self, *, alerts: AlertRepository, prices: PriceBarRepository) -> None:
        self._alerts = alerts
        self._prices = prices

    async def arm_price_alert(
        self,
        *,
        symbol: str,
        kind: AlertKind,
        price_level: Decimal,
        label: str,
    ) -> Alert:
        if kind not in (AlertKind.PRICE_ABOVE, AlertKind.PRICE_BELOW):
            raise ValueError("kind must be a price alert")
        alert = Alert(
            id=uuid.uuid4(),
            kind=kind,
            label=label,
            status=AlertStatus.ARMED,
            condition=AlertCondition(symbol=symbol.upper(), price_level=price_level),
            created_at=datetime.now(UTC),
        )
        return await self._alerts.add(alert)

    async def list(self) -> Sequence[Alert]:
        return await self._alerts.list_all()

    async def disable(self, alert_id: uuid.UUID) -> Alert | None:
        return await self._alerts.set_status(alert_id, AlertStatus.DISABLED)

    async def delete(self, alert_id: uuid.UUID) -> bool:
        return await self._alerts.delete(alert_id)

    async def sweep_price_alerts(self, *, timeframe: Timeframe = Timeframe.H1) -> SweepResult:
        """Walk every armed price alert and fire any whose condition is met
        against the latest stored close. Idempotent — alerts only fire
        once until re-armed."""
        rows = await self._alerts.list_armed()
        evaluated = 0
        fired = 0
        for row in rows:
            kind = AlertKind(row.kind)
            if kind not in (AlertKind.PRICE_ABOVE, AlertKind.PRICE_BELOW):
                continue
            evaluated += 1
            alert = await self._alerts.get(row.id)
            if alert is None or alert.condition.symbol is None:
                continue
            latest = await self._prices.latest(symbol=alert.condition.symbol, timeframe=timeframe)
            if latest is None:
                continue
            if evaluate_price_alert(alert, current_price=Decimal(latest.close)):
                await self._alerts.set_status(alert.id, AlertStatus.FIRED)
                fired += 1
                log.info(
                    "alert.fired",
                    id=str(alert.id),
                    kind=alert.kind.value,
                    symbol=alert.condition.symbol,
                    level=str(alert.condition.price_level),
                    close=str(latest.close),
                )
        return SweepResult(evaluated=evaluated, fired=fired)
