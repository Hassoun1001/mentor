"""Price-alert evaluation — pure function."""

from __future__ import annotations

from decimal import Decimal

from mentor.domain.alerts.alert import Alert, AlertKind


def evaluate_price_alert(alert: Alert, *, current_price: Decimal) -> bool:
    """Return True iff the alert's condition is currently satisfied."""
    if alert.condition.price_level is None:
        return False
    if alert.kind is AlertKind.PRICE_ABOVE:
        return current_price >= alert.condition.price_level
    if alert.kind is AlertKind.PRICE_BELOW:
        return current_price <= alert.condition.price_level
    return False
