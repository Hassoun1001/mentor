"""News ingestion + classification orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from mentor.domain.news.adapter import NewsAdapter
from mentor.domain.news.classifier import NewsClassifier
from mentor.infrastructure.repositories.news import NewsRepository
from mentor.logging import get_logger

log = get_logger("mentor.news.service")


@dataclass(frozen=True, slots=True)
class IngestionResult:
    fetched: int
    inserted: int
    classified: int


class NewsService:
    def __init__(
        self,
        *,
        adapter: NewsAdapter,
        classifier: NewsClassifier,
        repo: NewsRepository,
    ) -> None:
        self._adapter = adapter
        self._classifier = classifier
        self._repo = repo

    async def ingest_and_classify(
        self, *, query: str, since: datetime, classify_limit: int = 30
    ) -> IngestionResult:
        # 1) Fetch
        fetched = 0
        batch = []
        async for raw in self._adapter.fetch(query=query, since=since):
            batch.append(raw)
            fetched += 1
        inserted = await self._repo.upsert_raw(batch)

        # 2) Classify the newest unclassified items
        unclassified = await self._repo.list_unclassified(limit=classify_limit)
        classified = 0
        for orm in unclassified:
            classification = await self._classifier.classify(
                headline=orm.headline, summary=orm.summary
            )
            await self._repo.save_classification(orm.id, classification)
            classified += 1

        log.info(
            "news.ingest.done",
            fetched=fetched,
            inserted=inserted,
            classified=classified,
        )
        return IngestionResult(fetched=fetched, inserted=inserted, classified=classified)
