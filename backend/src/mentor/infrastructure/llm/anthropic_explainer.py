"""Anthropic-backed explainer.

Server-side only. The API key never leaves the backend; the frontend
calls `/api/v1/explain` and the response is the rendered explanation.
"""

from __future__ import annotations

from anthropic import AsyncAnthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from mentor.domain.explain.service import (
    ExplainerService,
    ExplainRequest,
    ExplainResponse,
)
from mentor.infrastructure.llm.prompts import SYSTEM_PROMPT, format_user_message
from mentor.logging import get_logger

log = get_logger("mentor.explain.anthropic")


class AnthropicExplainer(ExplainerService):
    def __init__(self, *, api_key: str, model: str, max_tokens: int = 800) -> None:
        if not api_key:
            raise ValueError("AnthropicExplainer requires an api_key")
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential_jitter(initial=0.5, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def explain(self, request: ExplainRequest) -> ExplainResponse:
        user = format_user_message(
            topic=request.topic, context=request.context, style=request.style
        )
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user}],
        )

        text_parts: list[str] = []
        for block in message.content:
            text = getattr(block, "text", None)
            if text:
                text_parts.append(text)
        explanation = "\n".join(text_parts).strip() or "(no explanation returned)"

        log.info(
            "explain.ok",
            topic=request.topic.value,
            model=self._model,
            input_tokens=getattr(message.usage, "input_tokens", None),
            output_tokens=getattr(message.usage, "output_tokens", None),
        )

        return ExplainResponse(
            topic=request.topic,
            explanation=explanation,
            source="anthropic",
        )
