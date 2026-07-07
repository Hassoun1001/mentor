"""Build the right explainer for the current environment.

If `ANTHROPIC_API_KEY` is set, we use the live LLM. Otherwise we fall
back to deterministic stubs so the rest of the app stays usable —
nothing in the user-facing flow should hard-fail because a secret is
missing.
"""

from __future__ import annotations

from functools import lru_cache

from mentor.config import get_settings
from mentor.domain.explain.service import ExplainerService
from mentor.infrastructure.llm import AnthropicExplainer, StubExplainer


@lru_cache(maxsize=1)
def build_explainer() -> ExplainerService:
    settings = get_settings()
    api_key = settings.anthropic_api_key.get_secret_value().strip()
    if not api_key:
        return StubExplainer()
    return AnthropicExplainer(api_key=api_key, model=settings.llm_model)


__all__ = ["build_explainer"]
