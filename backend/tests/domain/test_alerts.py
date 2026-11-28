"""Tests for the alert value object and price-alert evaluation."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from mentor.domain.alerts import (
    Alert,
    AlertCondition,
    AlertKind,
    AlertStatus,
    evaluate_price_alert,
)
from mentor.domain.errors import ValidationError

_LEVEL = Decimal("1.08500")


def _alert(
    kind: AlertKind,
    *,
    condition: AlertCondition | None = None,
    label: str = "EUR/USD level",
) -> Alert:
    return Alert(
        id=uuid.uuid4(),
        kind=kind,
        label=label,
        status=AlertStatus.ARMED,
        condition=condition or AlertCondition(symbol="EURUSD", price_level=_LEVEL),
        created_at=datetime(2026, 1, 5, 9, 0, tzinfo=UTC),
    )


class TestEvaluatePriceAlert:
    @pytest.mark.parametrize(
        ("price", "expected"),
        [("1.08499", False), ("1.08500", True), ("1.08501", True)],
    )
    def test_price_above_fires_at_or_above_the_level(self, price: str, expected: bool) -> None:
        alert = _alert(AlertKind.PRICE_ABOVE)
        assert evaluate_price_alert(alert, current_price=Decimal(price)) is expected

    @pytest.mark.parametrize(
        ("price", "expected"),
        [("1.08501", False), ("1.08500", True), ("1.08499", True)],
    )
    def test_price_below_fires_at_or_below_the_level(self, price: str, expected: bool) -> None:
        alert = _alert(AlertKind.PRICE_BELOW)
        assert evaluate_price_alert(alert, current_price=Decimal(price)) is expected

    @pytest.mark.parametrize("kind", [AlertKind.SIGNAL_CHANGE, AlertKind.EVENT_FREEZE])
    def test_non_price_kinds_never_fire_on_price(self, kind: AlertKind) -> None:
        # A level on a non-price alert must not turn it into a price watcher.
        condition = AlertCondition(symbol="EURUSD", price_level=_LEVEL, model_name="baseline")
        alert = _alert(kind, condition=condition)
        assert evaluate_price_alert(alert, current_price=Decimal("2")) is False
        assert evaluate_price_alert(alert, current_price=Decimal("0.5")) is False

    def test_missing_level_never_fires(self) -> None:
        alert = _alert(AlertKind.EVENT_FREEZE, condition=AlertCondition())
        assert evaluate_price_alert(alert, current_price=_LEVEL) is False


class TestAlertValidation:
    def test_blank_label_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc:
            _alert(AlertKind.PRICE_ABOVE, label="   ")
        assert exc.value.field == "label"

    @pytest.mark.parametrize("kind", [AlertKind.PRICE_ABOVE, AlertKind.PRICE_BELOW])
    def test_price_alert_requires_symbol(self, kind: AlertKind) -> None:
        with pytest.raises(ValidationError) as exc:
            _alert(kind, condition=AlertCondition(price_level=_LEVEL))
        assert exc.value.field == "symbol"

    @pytest.mark.parametrize("level", [None, Decimal("0"), Decimal("-1.1")])
    def test_price_alert_requires_positive_level(self, level: Decimal | None) -> None:
        with pytest.raises(ValidationError) as exc:
            _alert(
                AlertKind.PRICE_ABOVE,
                condition=AlertCondition(symbol="EURUSD", price_level=level),
            )
        assert exc.value.field == "price_level"

    def test_signal_change_requires_model_name(self) -> None:
        with pytest.raises(ValidationError) as exc:
            _alert(AlertKind.SIGNAL_CHANGE, condition=AlertCondition())
        assert exc.value.field == "model_name"

    def test_event_freeze_needs_no_price_fields(self) -> None:
        alert = _alert(AlertKind.EVENT_FREEZE, condition=AlertCondition())
        assert alert.status is AlertStatus.ARMED
