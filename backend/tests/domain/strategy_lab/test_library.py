"""The candidate library: well-formed, plain-spoken, and change-detecting."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.instruments import get_instrument
from mentor.domain.money import Money
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab.library import (
    CANDIDATES,
    MAX_GRID_SIZE,
    find_candidate,
    validate_library,
)
from mentor.domain.strategy_lab.rules import DonchianBreakout
from mentor.domain.strategy_lab.spec import ExitRules, StrategySpec


def test_starter_library_shape() -> None:
    assert 6 <= len(CANDIDATES) <= 10
    assert len({c.key for c in CANDIDATES}) == len(CANDIDATES)
    assert len({c.family for c in CANDIDATES}) == len(CANDIDATES), "families must be distinct"
    for c in CANDIDATES:
        assert 1 <= len(c.grid) <= MAX_GRID_SIZE
        assert len(c.hypothesis) > 80
        for spec in c.specs():
            text = spec.describe()
            assert "Risk 1% of the account" in text


def test_fingerprints_are_stable_and_notice_any_change() -> None:
    c = CANDIDATES[0]
    assert c.fingerprint() == find_candidate(c.key).fingerprint()  # type: ignore[union-attr]
    edited = replace(c, grid=c.grid[:-1])
    assert edited.fingerprint() != c.fingerprint()
    assert len({c.config_key(s) for s in c.specs()}) == len(c.grid)


def test_bad_definitions_are_refused() -> None:
    c = CANDIDATES[0]
    with pytest.raises(ValidationError):
        replace(c, key="Bad Key")
    with pytest.raises(ValidationError):
        replace(c, grid=c.grid + c.grid[:1])  # duplicate parameter set
    with pytest.raises(ValidationError):
        replace(c, grid=c.grid + CANDIDATES[1].grid[:1])  # two families
    with pytest.raises(ValidationError):
        validate_library([c, c])


def test_specs_demand_a_reason_and_a_sane_risk() -> None:
    rule, exits = DonchianBreakout(), ExitRules(stop_atr=2.0, target_r=None, max_bars=10)
    with pytest.raises(ValidationError):
        StrategySpec(rule=rule, exits=exits, timeframe=CANDIDATES[0].timeframe, hypothesis=" ")
    with pytest.raises(ValidationError):
        StrategySpec(
            rule=rule,
            exits=exits,
            timeframe=CANDIDATES[0].timeframe,
            hypothesis="x",
            risk_fraction=Decimal("0.05"),
        )
    with pytest.raises(ValidationError):
        ExitRules(stop_atr=0.0, target_r=None, max_bars=1)


def test_sizing_goes_through_the_risk_engine() -> None:
    spec = CANDIDATES[0].specs()[0]
    sizing = spec.size(
        account=Money(Decimal("10000"), "USD"),
        entry=Decimal("1.1000"),
        stop=Decimal("1.0950"),
        target=None,
        direction=Direction.LONG,
        instrument=get_instrument("EURUSD"),
    )
    # $100 at risk over 50 pips at $10/pip/lot → 0.2 lots
    assert sizing.lots == Decimal("0.20")
