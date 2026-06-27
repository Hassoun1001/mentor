"""Alert value object."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from mentor.domain.errors import ValidationError


class AlertKind(StrEnum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    SIGNAL_CHANGE = "signal_change"
    EVENT_FREEZE = "event_freeze"


class AlertStatus(StrEnum):
    ARMED = "armed"
    FIRED = "fired"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class AlertCondition:
    """Trigger condition payload.

    For price alerts: `price_level` is the threshold; `symbol` is the
    instrument it applies to.

    For signal alerts: `model_name` + the direction we want to be
    notified about (e.g. "flipped from long to short").

    For event-freeze: `category_min_impact` is the impact score above
    which we consider an event "high-impact."
    """

    symbol: str | None = None
    price_level: Decimal | None = None
    model_name: str | None = None
    target_direction: str | None = None
    category_min_impact: Decimal | None = None
    freeze_minutes_before: int = 30
    freeze_minutes_after: int = 30


@dataclass(frozen=True, slots=True)
class Alert:
    id: uuid.UUID
    kind: AlertKind
    label: str
    status: AlertStatus
    condition: AlertCondition
    created_at: datetime
    fired_at: datetime | None = None
    last_evaluated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValidationError("label required", field="label")
        if self.kind in (AlertKind.PRICE_ABOVE, AlertKind.PRICE_BELOW):
            if not self.condition.symbol:
                raise ValidationError("price alerts require a symbol", field="symbol")
            if self.condition.price_level is None or self.condition.price_level <= 0:
                raise ValidationError(
                    "price alerts require a positive price_level",
                    field="price_level",
                )
        if self.kind is AlertKind.SIGNAL_CHANGE and not self.condition.model_name:
            raise ValidationError("signal-change alerts require a model_name", field="model_name")
