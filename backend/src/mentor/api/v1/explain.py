"""Contextual explainer endpoint."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from mentor.application.explain import build_explainer
from mentor.domain.explain.service import ExplainRequest, SupportedTopic

router = APIRouter(prefix="/explain", tags=["explain"])


class ExplainRequestBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic": "position-size",
                "context": {
                    "symbol": "EURUSD",
                    "account": "10000 USD",
                    "risk_pct": "1",
                    "entry": "1.08500",
                    "stop": "1.08200",
                    "lots": "0.33",
                },
                "style": "concise",
            }
        }
    )

    topic: SupportedTopic
    context: dict[str, Any] = Field(default_factory=dict, max_length=64)
    style: Literal["concise", "thorough"] = "concise"


class ExplainResponseBody(BaseModel):
    topic: SupportedTopic
    explanation: str
    source: str


@router.post("", response_model=ExplainResponseBody)
async def explain(body: ExplainRequestBody) -> ExplainResponseBody:
    explainer = build_explainer()
    result = await explainer.explain(
        ExplainRequest(topic=body.topic, context=body.context, style=body.style)
    )
    return ExplainResponseBody(
        topic=result.topic, explanation=result.explanation, source=result.source
    )
