"""Deterministic stub explainer.

Used when no Anthropic API key is configured. Returns a context-aware
templated explanation — honest about its lack of LLM reasoning — so the
UI is functional out of the box without secrets.
"""

from __future__ import annotations

from mentor.domain.explain.service import (
    ExplainerService,
    ExplainRequest,
    ExplainResponse,
    SupportedTopic,
)

_TEMPLATES: dict[SupportedTopic, str] = {
    SupportedTopic.POSITION_SIZE: (
        "Position size is sized from your account, stop distance, and risk "
        "percentage. With the current inputs the calculator landed on the "
        "rounded value shown; if it rounded to 0, your risk budget cannot "
        "afford the broker's minimum lot for this stop distance. "
        "(Anthropic key not configured — this is a templated explanation.)"
    ),
    SupportedTopic.PIP_VALUE: (
        "Pip value is contract size × pip size × quote-to-account rate × lots. "
        "It is the cash that one pip's worth of price movement is worth at "
        "your chosen lot size, in your account currency. "
        "(Anthropic key not configured — templated explanation.)"
    ),
    SupportedTopic.PIP_DISTANCE: (
        "Pip distance is just |entry - stop| / pip_size. Wider stop distances "
        "mean smaller positions for the same risk budget. "
        "(Anthropic key not configured — templated explanation.)"
    ),
    SupportedTopic.RISK_REWARD: (
        "R:R = reward distance / risk distance. A 1:2 trade can be wrong "
        "more than half the time and still profit; below 1:1 you need a "
        "very high win rate. "
        "(Anthropic key not configured — templated explanation.)"
    ),
    SupportedTopic.MONEY_AT_RISK: (
        "Money at risk is the cash you lose if the trade hits its stop at "
        "the rounded size. It is always ≤ your stated risk budget. "
        "(Anthropic key not configured — templated explanation.)"
    ),
    SupportedTopic.EXPECTANCY: (
        "Expectancy is (win% × avg win R) − (loss% × avg loss R). A small "
        "sample is dominated by variance; large samples reveal the real "
        "edge. "
        "(Anthropic key not configured — templated explanation.)"
    ),
    SupportedTopic.R_MULTIPLE: (
        "An R-multiple is a trade's outcome divided by its initial risk. "
        "A full stop-out is -1R; a 2x-risk win is +2R. R normalises across "
        "account sizes. "
        "(Anthropic key not configured — templated explanation.)"
    ),
    SupportedTopic.WIN_RATE: (
        "Win rate alone says nothing about profitability — pair it with "
        "average R:R to talk about expectancy. "
        "(Anthropic key not configured — templated explanation.)"
    ),
    SupportedTopic.PROFIT_FACTOR: (
        "Profit factor is gross wins / gross losses. Above 1 means net "
        "winning; below 1 means net losing. "
        "(Anthropic key not configured — templated explanation.)"
    ),
    SupportedTopic.GUARDRAILS: (
        "Guardrails block trades that breach per-trade, portfolio, or "
        "daily loss limits. The daily loss limit matters most — it stops "
        "tilt before it compounds. "
        "(Anthropic key not configured — templated explanation.)"
    ),
    SupportedTopic.ATR_STOP: (
        "An ATR-scaled stop sits at a multiple of recent volatility, so "
        "the same setup gets a wider stop on a wild day and a tighter one "
        "on a calm day. Standard multiplier: 2–3× ATR. "
        "(Anthropic key not configured — templated explanation.)"
    ),
}


class StubExplainer(ExplainerService):
    async def explain(self, request: ExplainRequest) -> ExplainResponse:
        text = _TEMPLATES.get(
            request.topic,
            "No templated explanation available — configure ANTHROPIC_API_KEY.",
        )
        return ExplainResponse(topic=request.topic, explanation=text, source="stub")
