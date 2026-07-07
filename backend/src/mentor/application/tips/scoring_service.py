"""Tip scoring — pull live prices and build the tipster's track record."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.domain.tips.scoring import (
    Scorecard,
    TipOutcome,
    build_outcome,
    build_scorecard,
)
from mentor.domain.tips.vol_context import build_ticker_vol_context
from mentor.infrastructure.adapters.stock_quotes import (
    DailyClose,
    StockQuoteClient,
    StockQuoteError,
)
from mentor.infrastructure.models import StockTipORM
from mentor.infrastructure.repositories.stock_tips import StockTipRepository
from mentor.logging import get_logger

log = get_logger("mentor.tips.scoring")


@dataclass(frozen=True, slots=True)
class ScoredTips:
    tipster: str
    outcomes: tuple[TipOutcome, ...]
    scorecard: Scorecard
    unpriced: tuple[str, ...]


class TipScoringService:
    def __init__(self, *, repo: StockTipRepository, quotes: StockQuoteClient) -> None:
        self._repo = repo
        self._quotes = quotes

    async def _load_series(
        self, priced: Sequence[StockTipORM], now: datetime
    ) -> tuple[dict[str, list[DailyClose]], list[str]]:
        """One quote pull per distinct ticker, covering the whole span.

        We reach back ~120 days before the earliest mention so there's enough
        history for the per-ticker volatility read, even for very recent tips.
        The since-mention stats only use closes on/after the mention date, so
        the extra lead-in doesn't affect them.
        """
        earliest = min(t.mentioned_at for t in priced)
        series: dict[str, list[DailyClose]] = {}
        unpriced: list[str] = []
        for ticker in dict.fromkeys(t.ticker for t in priced):
            try:
                series[ticker] = await self._quotes.daily_closes(
                    ticker=ticker, start=earliest - timedelta(days=120), end=now + timedelta(days=1)
                )
            except StockQuoteError:
                unpriced.append(ticker)
        return series, unpriced

    async def score(self, *, tipster: str | None = None) -> ScoredTips:
        tips = await self._repo.list_all(tipster=tipster)
        priced = [t for t in tips if t.mention_price is not None]
        if not priced:
            label = tipster or "all tipsters"
            return ScoredTips(
                tipster=label,
                outcomes=(),
                scorecard=build_scorecard(tipster=label, outcomes=[]),
                unpriced=tuple(dict.fromkeys(t.ticker for t in tips)),
            )

        now = datetime.now(UTC)
        series, unpriced = await self._load_series(priced, now)

        outcomes: list[TipOutcome] = []
        for t in priced:
            closes = series.get(t.ticker) or []
            if not closes:
                unpriced.append(t.ticker)
                continue
            outcomes.append(_outcome_for(t, closes, now))

        distinct_tipsters = {p.tipster for p in priced}
        label = tipster or (priced[0].tipster if len(distinct_tipsters) == 1 else "all")
        card = build_scorecard(tipster=label, outcomes=outcomes)
        log.info("tips.scored", tipster=label, outcomes=len(outcomes))
        return ScoredTips(
            tipster=label,
            outcomes=tuple(outcomes),
            scorecard=card,
            unpriced=tuple(dict.fromkeys(unpriced)),
        )

    async def outcomes_by_tipster(self) -> dict[str, list[TipOutcome]]:
        """Every tipster's realised outcomes, grouped — one quote pull per
        distinct ticker across all tips (the leaderboard's data source)."""
        tips = await self._repo.list_all(tipster=None)
        priced = [t for t in tips if t.mention_price is not None]
        if not priced:
            return {}
        now = datetime.now(UTC)
        series, _ = await self._load_series(priced, now)
        grouped: dict[str, list[TipOutcome]] = {}
        for t in priced:
            closes = series.get(t.ticker) or []
            if not closes:
                continue
            grouped.setdefault(t.tipster, []).append(_outcome_for(t, closes, now))
        return grouped


def _outcome_for(tip: StockTipORM, closes: Sequence[DailyClose], now: datetime) -> TipOutcome:
    mention_price = tip.mention_price
    assert mention_price is not None  # caller filters to priced tips
    since = [c for c in closes if c.day >= tip.mentioned_at]
    window = since or list(closes)
    current = window[-1].close
    prices = [c.close for c in window]
    outcome = build_outcome(
        ticker=tip.ticker,
        category=tip.category,
        action=tip.action,
        conviction=tip.conviction,
        note=tip.note,
        days_held=max(0, (now - tip.mentioned_at).days),
        mention_price=Decimal(mention_price),
        current_price=current,
        min_since=min(prices),
        max_since=max(prices),
    )
    # Objective vol context + today's move, both from the close series we
    # already fetched (no extra network calls).
    prices_all = [c.close for c in closes]
    daily = None
    if len(prices_all) >= 2 and prices_all[-2] > 0:
        daily = ((prices_all[-1] - prices_all[-2]) / prices_all[-2] * Decimal("100")).quantize(
            Decimal("0.01")
        )
    ctx = build_ticker_vol_context(prices_all)
    return replace(
        outcome,
        daily_change_pct=daily,
        expected_move_pct=ctx.expected_move_pct if ctx else None,
        vol_regime=ctx.regime.value if ctx else None,
    )
