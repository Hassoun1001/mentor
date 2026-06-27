"""NewsItem persistence."""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import CursorResult, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.domain.news.adapter import RawNewsItem
from mentor.domain.news.classifier import NewsCategory, NewsClassification
from mentor.domain.news.item import NewsItem
from mentor.infrastructure.models import NewsItemORM


def _hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _to_domain(orm: NewsItemORM) -> NewsItem:
    classification: NewsClassification | None = None
    if orm.category and orm.impact is not None and orm.confidence is not None:
        classification = NewsClassification(
            category=NewsCategory(orm.category),
            impact=Decimal(orm.impact),
            confidence=Decimal(orm.confidence),
            rationale=orm.rationale or "(no rationale stored)",
        )
    return NewsItem(
        id=orm.id,
        source=orm.source,
        url=orm.url,
        ts=orm.ts,
        headline=orm.headline,
        summary=orm.summary,
        classification=classification,
    )


class NewsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_raw(self, items: Iterable[RawNewsItem]) -> int:
        """Insert new headlines; existing url_hashes are skipped."""
        rows = [
            {
                "id": uuid.uuid4(),
                "source": item.source[:64],
                "url": item.url,
                "url_hash": _hash(item.url),
                "ts": item.ts,
                "headline": item.headline,
                "summary": item.summary,
            }
            for item in items
            if item.url
        ]
        if not rows:
            return 0
        stmt = (
            pg_insert(NewsItemORM).values(rows).on_conflict_do_nothing(index_elements=["url_hash"])
        )
        result = cast("CursorResult[Any]", await self._session.execute(stmt))
        return result.rowcount or 0

    async def list_unclassified(self, limit: int = 50) -> Sequence[NewsItemORM]:
        stmt = (
            select(NewsItemORM)
            .where(NewsItemORM.category.is_(None))
            .order_by(NewsItemORM.ts.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def save_classification(
        self, item_id: uuid.UUID, classification: NewsClassification
    ) -> None:
        orm = await self._session.get(NewsItemORM, item_id)
        if orm is None:
            return
        orm.category = classification.category.value
        orm.impact = classification.impact
        orm.confidence = classification.confidence
        orm.rationale = classification.rationale
        orm.classified_at = datetime.now(UTC)
        await self._session.flush()

    async def recent(
        self,
        *,
        limit: int = 50,
        only_classified: bool = False,
        min_impact: Decimal | None = None,
    ) -> list[NewsItem]:
        stmt = select(NewsItemORM).order_by(NewsItemORM.ts.desc()).limit(limit)
        if only_classified:
            stmt = stmt.where(NewsItemORM.category.is_not(None))
        if min_impact is not None:
            stmt = stmt.where(NewsItemORM.impact >= min_impact)
        result = await self._session.execute(stmt)
        return [_to_domain(o) for o in result.scalars().all()]
