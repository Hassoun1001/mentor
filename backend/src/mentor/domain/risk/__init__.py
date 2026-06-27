"""Risk engine — Phase 0 of the plan.

> Most traders fail on risk management, not forecasting. The risk engine is
> the foundation and is built first.
"""

from mentor.domain.risk.expectancy import Expectancy, expectancy, r_multiple
from mentor.domain.risk.guardrails import (
    Breach,
    GuardrailLimits,
    GuardrailReport,
    OpenPosition,
    check_guardrails,
)
from mentor.domain.risk.monte_carlo import MonteCarloResult, simulate_risk_of_ruin
from mentor.domain.risk.position_sizing import (
    Direction,
    PositionSizing,
    RiskInputs,
    calculate_position,
)
from mentor.domain.risk.stops import atr_stop_distance

__all__ = [
    "Breach",
    "Direction",
    "Expectancy",
    "GuardrailLimits",
    "GuardrailReport",
    "MonteCarloResult",
    "OpenPosition",
    "PositionSizing",
    "RiskInputs",
    "atr_stop_distance",
    "calculate_position",
    "check_guardrails",
    "expectancy",
    "r_multiple",
    "simulate_risk_of_ruin",
]
