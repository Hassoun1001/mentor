"""LLM-backed explainer + classifier adapters."""

from mentor.infrastructure.llm.anthropic_explainer import AnthropicExplainer
from mentor.infrastructure.llm.news_classifier import (
    AnthropicNewsClassifier,
    StubNewsClassifier,
    build_news_classifier,
)
from mentor.infrastructure.llm.stub_explainer import StubExplainer

__all__ = [
    "AnthropicExplainer",
    "AnthropicNewsClassifier",
    "StubExplainer",
    "StubNewsClassifier",
    "build_news_classifier",
]
