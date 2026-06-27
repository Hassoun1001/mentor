"""Build the right explainer for the current environment.

If `ANTHROPIC_API_KEY` is set, we use the live LLM. Otherwise we fall
back to deterministic stubs so the rest of the app stays usable —
nothing in the user-facing flow should hard-fail because a secret is
missing.
"""

from __future__ import annotations

import os
from functools import lru_cache

from mentor.domain.explain.service import ExplainerService
from mentor.infrastructure.llm import AnthropicExplainer, StubExplainer


@lru_cache(maxsize=1)
def build_explainer() -> ExplainerService:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return StubExplainer()
    return AnthropicExplainer(
        api_key=api_key,
        model=os.environ.get("MENTOR_LLM_MODEL", "claude-opus-4-7") or "claude-opus-4-7",
    )


__all__ = ["build_explainer"]
