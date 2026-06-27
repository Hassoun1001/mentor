"""Stub news classifier tests."""

from __future__ import annotations

import pytest

from mentor.domain.news.classifier import NewsCategory
from mentor.infrastructure.llm.news_classifier import StubNewsClassifier


@pytest.mark.parametrize(
    "headline, expected",
    [
        ("ECB rate decision: 25 bps cut expected", NewsCategory.MACRO),
        ("New tariff order signed by US president", NewsCategory.REGULATORY),
        ("Conflict escalates in border region", NewsCategory.GEOPOLITICAL),
        ("EUR/USD surges 5% on the news", NewsCategory.HYPE),
        ("Local cafe wins award", NewsCategory.OTHER),
    ],
)
async def test_stub_classifier_assigns_expected_category(
    headline: str, expected: NewsCategory
) -> None:
    classifier = StubNewsClassifier()
    out = await classifier.classify(headline=headline, summary=None)
    assert out.category is expected
    assert 0 <= out.impact <= 1
    assert 0 <= out.confidence <= 1
