"""Explainer domain — Phase 2.

> Tap any metric (RSI, position size, R:R, confidence) for a plain-language
> explanation computed from the live values.   — Mentor product plan, §6.A

The interface is provider-agnostic. Concrete adapters (Anthropic, stub,
mock) live in `infrastructure/llm`. Domain code never imports the SDK.
"""

from mentor.domain.explain.service import (
    ExplainerService,
    ExplainRequest,
    ExplainResponse,
    SupportedTopic,
)

__all__ = ["ExplainRequest", "ExplainResponse", "ExplainerService", "SupportedTopic"]
