"""Yahoo analyst coverage — free consensus target + per-firm ratings.

Yahoo's quoteSummary now requires a cookie + crumb, so we do that handshake
once per client and reuse it. Everything is best-effort: any failure (rate
limit, missing module, shape change) returns ``None`` and the tips UI simply
omits the analyst panel rather than erroring.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from mentor.domain.tips.analyst import (
    AnalystConsensus,
    AnalystProvider,
    AnalystRating,
    AnalystSnapshot,
    compute_upside,
    latest_per_firm,
    match_firm,
)

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)
_MODULES = "financialData,recommendationTrend,upgradeDowngradeHistory,price"


def _num(d: dict[str, Any], key: str) -> Decimal | None:
    v = d.get(key)
    if isinstance(v, dict):
        v = v.get("raw")
    if v is None:
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError):
        return None


def _int(d: dict[str, Any], key: str) -> int | None:
    n = _num(d, key)
    return int(n) if n is not None else None


class YahooAnalystProvider(AnalystProvider):
    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        self._owns = client is None
        self._client = client or httpx.AsyncClient(
            timeout=20.0, headers={"User-Agent": _UA}, follow_redirects=True
        )
        self._crumb: str | None = None

    async def aclose(self) -> None:
        if self._owns:
            await self._client.aclose()

    async def _ensure_crumb(self) -> None:
        if self._crumb:
            return
        # cookies are best-effort; getcrumb may still work without them
        with contextlib.suppress(httpx.HTTPError):
            await self._client.get("https://fc.yahoo.com")
        r = await self._client.get("https://query2.finance.yahoo.com/v1/test/getcrumb")
        self._crumb = r.text.strip()

    async def fetch(self, ticker: str) -> AnalystSnapshot | None:
        try:
            await self._ensure_crumb()
            url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker.upper()}"
            resp = await self._client.get(url, params={"modules": _MODULES, "crumb": self._crumb})
            if resp.status_code != 200:
                return None
            results = resp.json().get("quoteSummary", {}).get("result") or []
            if not results:
                return None
            data = results[0]
        except (httpx.HTTPError, ValueError, KeyError):
            return None

        fin = data.get("financialData") or {}
        current = _num(fin, "currentPrice")
        target_mean = _num(fin, "targetMeanPrice")

        trend = (data.get("recommendationTrend") or {}).get("trend") or [{}]
        t0 = trend[0]
        consensus = AnalystConsensus(
            target_mean=target_mean,
            target_high=_num(fin, "targetHighPrice"),
            target_low=_num(fin, "targetLowPrice"),
            upside_pct=compute_upside(target_mean, current),
            rating_key=fin.get("recommendationKey"),
            num_analysts=_int(fin, "numberOfAnalystOpinions"),
            strong_buy=_int(t0, "strongBuy") or 0,
            buy=_int(t0, "buy") or 0,
            hold=_int(t0, "hold") or 0,
            sell=_int(t0, "sell") or 0,
            strong_sell=_int(t0, "strongSell") or 0,
        )

        history = (data.get("upgradeDowngradeHistory") or {}).get("history") or []
        ratings: list[AnalystRating] = []
        for h in history:
            firm = match_firm(str(h.get("firm", "")))
            if firm is None:
                continue
            epoch = h.get("epochGradeDate")
            grade = h.get("toGrade")
            if not isinstance(epoch, (int, float)) or not grade:
                continue
            ratings.append(
                AnalystRating(
                    firm=firm,
                    rating=str(grade),
                    action=str(h.get("action", "")),
                    date=datetime.fromtimestamp(int(epoch), UTC),
                )
            )

        return AnalystSnapshot(
            ticker=ticker.upper(),
            current_price=current,
            consensus=consensus if target_mean is not None or consensus.num_analysts else None,
            ratings=latest_per_firm(ratings),
        )
