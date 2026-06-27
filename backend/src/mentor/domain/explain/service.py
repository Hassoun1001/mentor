"""Explainer contract.

The mentor never produces verdicts ("buy this"). It explains the
reasoning behind a metric, names what would change the call, and uses
the *actual* numbers the user is looking at — not a generic textbook
explanation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class SupportedTopic(StrEnum):
    """Whitelist of metrics the explainer knows about.

    The whitelist is deliberate: a user-supplied free-text topic would let
    a prompt-injection payload masquerade as a metric. We accept only the
    known topics; the user can ask for arbitrary follow-ups through a
    different (future) endpoint, never through this one.
    """

    POSITION_SIZE = "position-size"
    PIP_VALUE = "pip-value"
    PIP_DISTANCE = "pip-distance"
    RISK_REWARD = "risk-reward"
    MONEY_AT_RISK = "money-at-risk"
    EXPECTANCY = "expectancy"
    R_MULTIPLE = "r-multiple"
    WIN_RATE = "win-rate"
    PROFIT_FACTOR = "profit-factor"
    GUARDRAILS = "guardrails"
    ATR_STOP = "atr-stop"


@dataclass(frozen=True, slots=True)
class ExplainRequest:
    topic: SupportedTopic
    context: dict[str, Any]
    style: str = "concise"  # "concise" or "thorough"


@dataclass(frozen=True, slots=True)
class ExplainResponse:
    topic: SupportedTopic
    explanation: str
    source: str  # "anthropic" | "stub" | "cache"


class ExplainerService(ABC):
    @abstractmethod
    async def explain(self, request: ExplainRequest) -> ExplainResponse: ...
