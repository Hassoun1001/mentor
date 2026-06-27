"""NewsAPI.org adapter.

The free tier serves headline-only items, which is fine for the
classifier — the LLM scores headlines well and pulling article bodies
would multiply both cost and prompt-injection surface.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any, Final

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from mentor.domain.errors import DomainError
from mentor.domain.news.adapter import NewsAdapter, RawNewsItem


class NewsApiError(DomainError):
    pass


class NewsApiAdapter(NewsAdapter):
    name = "newsapi"
    _BASE_URL: Final = "https://newsapi.org/v2"

    def __init__(self, *, api_key: str, client: httpx.AsyncClient | None = None) -> None:
        if not api_key:
            raise ValueError("NewsApiAdapter requires an api_key")
        self._api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        wait=wait_exponential_jitter(initial=0.5, max=8),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    async def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        response = await self._client.get(
            f"{self._BASE_URL}{path}",
            params={**params, "apiKey": self._api_key},
        )
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        if body.get("status") != "ok":
            raise NewsApiError(body.get("message", "NewsAPI returned error"))
        return body

    async def fetch(self, *, query: str, since: datetime) -> AsyncIterator[RawNewsItem]:
        params = {
            "q": query,
            "from": since.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S"),
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": "50",
        }
        body = await self._get("/everything", params)
        articles = body.get("articles") or []
        for article in articles:
            published_at = article.get("publishedAt")
            if not published_at:
                continue
            yield RawNewsItem(
                source=(article.get("source") or {}).get("name", "newsapi"),
                url=article.get("url", ""),
                ts=_parse_iso(published_at),
                headline=article.get("title", "") or "(untitled)",
                summary=article.get("description"),
            )


def _parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt
