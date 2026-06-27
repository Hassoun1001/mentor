"""News domain — Phase 4.

> Pulls headlines and articles relevant to the instrument from financial
> news sources. The model classifies each story (macro, regulatory,
> geopolitical, risk-off, hype) and scores likely impact and confidence.
> — Mentor product plan, §6.C

News flows: adapter → classifier → storage → forecast input. The
adapter never decides what's relevant; the classifier never fetches.
"""

from mentor.domain.news.adapter import NewsAdapter, RawNewsItem
from mentor.domain.news.classifier import (
    NewsCategory,
    NewsClassification,
    NewsClassifier,
)
from mentor.domain.news.item import NewsItem

__all__ = [
    "NewsAdapter",
    "NewsCategory",
    "NewsClassification",
    "NewsClassifier",
    "NewsItem",
    "RawNewsItem",
]
