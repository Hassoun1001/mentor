"""News endpoints."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mentor.api.deps import SessionDep
from mentor.application.news import NewsService
from mentor.domain.news.classifier import NewsCategory
from mentor.infrastructure.adapters.news import NewsApiAdapter
from mentor.infrastructure.llm import build_news_classifier
from mentor.infrastructure.repositories import NewsRepository

router = APIRouter(prefix="/news", tags=["news"])


class IngestRequest(BaseModel):
    query: str = Field(default="EUR USD forex")
    hours_back: int = Field(default=24, ge=1, le=720)


class IngestResponse(BaseModel):
    fetched: int
    inserted: int
    classified: int


@router.post("/ingest", response_model=IngestResponse)
async def ingest(body: IngestRequest, session: SessionDep) -> IngestResponse:
    api_key = os.environ.get("NEWSAPI_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="NEWSAPI_KEY not configured — add it to .env to ingest news.",
        )
    adapter = NewsApiAdapter(api_key=api_key)
    classifier = build_news_classifier()
    repo = NewsRepository(session)
    service = NewsService(adapter=adapter, classifier=classifier, repo=repo)

    since = datetime.now(UTC) - timedelta(hours=body.hours_back)
    try:
        result = await service.ingest_and_classify(query=body.query, since=since)
    finally:
        await adapter.aclose()
    return IngestResponse(
        fetched=result.fetched, inserted=result.inserted, classified=result.classified
    )


class NewsClassificationDTO(BaseModel):
    category: NewsCategory
    impact: Decimal
    confidence: Decimal
    rationale: str


class NewsItemDTO(BaseModel):
    id: uuid.UUID
    source: str
    url: str
    ts: datetime
    headline: str
    summary: str | None
    classification: NewsClassificationDTO | None


@router.get("", response_model=list[NewsItemDTO])
async def recent(
    session: SessionDep,
    limit: int = 50,
    only_classified: bool = False,
    min_impact: Decimal | None = None,
) -> list[NewsItemDTO]:
    items = await NewsRepository(session).recent(
        limit=limit, only_classified=only_classified, min_impact=min_impact
    )
    return [
        NewsItemDTO(
            id=item.id,
            source=item.source,
            url=item.url,
            ts=item.ts,
            headline=item.headline,
            summary=item.summary,
            classification=(
                NewsClassificationDTO(
                    category=item.classification.category,
                    impact=item.classification.impact,
                    confidence=item.classification.confidence,
                    rationale=item.classification.rationale,
                )
                if item.classification
                else None
            ),
        )
        for item in items
    ]
