"""Stock-tip tracker endpoints.

Ingest a tipster's message, snapshot entry prices, and score the calls
that follow. This is a *track record*, never advice — the disclaimers are
part of the payload so the UI can't forget them.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mentor.api.deps import SessionDep
from mentor.application.tips import (
    LeaderboardService,
    TipBacktestService,
    TipIngestService,
    TipScoringService,
)
from mentor.domain.errors import DomainError
from mentor.infrastructure.adapters.analyst_yahoo import YahooAnalystProvider
from mentor.infrastructure.adapters.stock_quotes import StockQuoteClient
from mentor.infrastructure.llm.tip_parser import build_tip_parser
from mentor.infrastructure.repositories.stock_tips import StockTipRepository

router = APIRouter(prefix="/tips", tags=["tips"])


class IngestTipsRequest(BaseModel):
    tipster: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1)
    mentioned_at: datetime | None = None


class IngestedTipDTO(BaseModel):
    ticker: str
    category: str
    action: str
    conviction: str
    mention_price: Decimal | None


class IngestTipsResponse(BaseModel):
    tipster: str
    parsed: int
    priced: int
    unpriced_tickers: list[str]
    tips: list[IngestedTipDTO]


@router.post("/ingest", response_model=IngestTipsResponse)
async def ingest_tips(body: IngestTipsRequest, session: SessionDep) -> IngestTipsResponse:
    try:
        parser = build_tip_parser()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    quotes = StockQuoteClient()
    try:
        service = TipIngestService(
            parser=parser, repo=StockTipRepository(session), quotes=quotes
        )
        result = await service.ingest(
            tipster=body.tipster, text=body.text, mentioned_at=body.mentioned_at
        )
    except DomainError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        await quotes.aclose()

    return IngestTipsResponse(
        tipster=result.tipster,
        parsed=result.parsed,
        priced=result.priced,
        unpriced_tickers=list(result.unpriced_tickers),
        tips=[
            IngestedTipDTO(
                ticker=t.ticker,
                category=t.category,
                action=t.action,
                conviction=t.conviction,
                mention_price=t.mention_price,
            )
            for t in result.tips
        ],
    )


class OutcomeDTO(BaseModel):
    ticker: str
    category: str
    action: str
    conviction: str
    note: str
    days_held: int
    mention_price: Decimal
    current_price: Decimal
    return_pct: Decimal
    max_drawup_pct: Decimal
    max_drawdown_pct: Decimal
    dipped: bool | None
    expected_move_pct: Decimal | None
    vol_regime: str | None
    at_or_below_entry: bool
    daily_change_pct: Decimal | None


class BucketDTO(BaseModel):
    key: str
    count: int
    mean_return_pct: Decimal
    win_rate: Decimal
    avg_days_held: Decimal
    best_ticker: str | None
    best_return_pct: Decimal
    worst_ticker: str | None
    worst_return_pct: Decimal


class ScorecardDTO(BaseModel):
    tipster: str
    total: int
    overall: BucketDTO
    by_category: list[BucketDTO]
    by_action: list[BucketDTO]
    dip_accuracy: Decimal | None
    headline: str


class ScoredResponse(BaseModel):
    tipster: str
    scorecard: ScorecardDTO
    outcomes: list[OutcomeDTO]
    unpriced: list[str]


def _bucket_dto(b) -> BucketDTO:  # type: ignore[no-untyped-def]
    return BucketDTO(
        key=b.key,
        count=b.count,
        mean_return_pct=b.mean_return_pct,
        win_rate=b.win_rate,
        avg_days_held=b.avg_days_held,
        best_ticker=b.best_ticker,
        best_return_pct=b.best_return_pct,
        worst_ticker=b.worst_ticker,
        worst_return_pct=b.worst_return_pct,
    )


@router.get("/scored", response_model=ScoredResponse)
async def scored(session: SessionDep, tipster: str | None = None) -> ScoredResponse:
    """Live returns since mention + the tipster's aggregated scorecard."""
    quotes = StockQuoteClient()
    try:
        service = TipScoringService(repo=StockTipRepository(session), quotes=quotes)
        result = await service.score(tipster=tipster)
    finally:
        await quotes.aclose()

    card = result.scorecard
    return ScoredResponse(
        tipster=result.tipster,
        scorecard=ScorecardDTO(
            tipster=card.tipster,
            total=card.total,
            overall=_bucket_dto(card.overall),
            by_category=[_bucket_dto(b) for b in card.by_category],
            by_action=[_bucket_dto(b) for b in card.by_action],
            dip_accuracy=card.dip_accuracy,
            headline=card.headline,
        ),
        outcomes=[
            OutcomeDTO(
                ticker=o.ticker,
                category=o.category,
                action=o.action,
                conviction=o.conviction,
                note=o.note,
                days_held=o.days_held,
                mention_price=o.mention_price,
                current_price=o.current_price,
                return_pct=o.return_pct,
                max_drawup_pct=o.max_drawup_pct,
                max_drawdown_pct=o.max_drawdown_pct,
                dipped=o.dipped,
                expected_move_pct=o.expected_move_pct,
                vol_regime=o.vol_regime,
                at_or_below_entry=o.at_or_below_entry,
                daily_change_pct=o.daily_change_pct,
            )
            for o in result.outcomes
        ],
        unpriced=list(result.unpriced),
    )


@router.get("/tipsters", response_model=list[str])
async def tipsters(session: SessionDep) -> list[str]:
    return await StockTipRepository(session).tipsters()


# ---------- leaderboard ----------


class LeaderboardRowDTO(BaseModel):
    tipster: str
    tracked_calls: int
    mean_return_pct: Decimal
    win_rate: Decimal
    return_stdev: Decimal
    risk_adjusted: Decimal
    best_ticker: str | None
    best_return_pct: Decimal
    avg_days_held: Decimal


@router.get("/leaderboard", response_model=list[LeaderboardRowDTO])
async def leaderboard(session: SessionDep) -> list[LeaderboardRowDTO]:
    """Rank every tipster by risk-adjusted return. Measurement, not advice."""
    quotes = StockQuoteClient()
    try:
        scoring = TipScoringService(repo=StockTipRepository(session), quotes=quotes)
        rows = await LeaderboardService(scoring=scoring).rank()
    finally:
        await quotes.aclose()
    return [
        LeaderboardRowDTO(
            tipster=r.tipster,
            tracked_calls=r.tracked_calls,
            mean_return_pct=r.mean_return_pct,
            win_rate=r.win_rate,
            return_stdev=r.return_stdev,
            risk_adjusted=r.risk_adjusted,
            best_ticker=r.best_ticker,
            best_return_pct=r.best_return_pct,
            avg_days_held=r.avg_days_held,
        )
        for r in rows
    ]


# ---------- "follow him" backtest ----------


class BacktestRequest(BaseModel):
    tipster: str
    starting_equity: Decimal = Field(default=Decimal("10000"), gt=0)
    risk_pct: Decimal = Field(default=Decimal("0.01"), gt=0, le=Decimal("0.5"))
    stop_pct: Decimal = Field(default=Decimal("0.10"), gt=0, lt=Decimal("1"))
    apply_stop: bool = True


class FollowTradeDTO(BaseModel):
    ticker: str
    mentioned_at: datetime
    entry_price: Decimal
    exit_fill: Decimal
    stop_price: Decimal
    shares: Decimal
    risk_amount: Decimal
    pnl: Decimal
    r_multiple: Decimal
    return_pct: Decimal
    days_held: int
    stopped_out: bool
    won: bool


class EquityPointDTO(BaseModel):
    label: str
    at: datetime
    equity: Decimal


class BacktestResponse(BaseModel):
    tipster: str
    starting_equity: Decimal
    ending_equity: Decimal
    risk_pct: Decimal
    stop_pct: Decimal
    apply_stop: bool
    n_trades: int
    total_return_pct: Decimal
    max_drawdown_pct: Decimal
    expectancy_r: Decimal
    win_rate: Decimal
    avg_days_held: Decimal
    equity_curve: list[EquityPointDTO]
    trades: list[FollowTradeDTO]
    headline: str
    disclaimer: str = (
        "A mechanical simulation of already-known outcomes, not a prediction "
        "or advice. Past calls do not predict future ones."
    )


@router.post("/backtest", response_model=BacktestResponse)
async def backtest(body: BacktestRequest, session: SessionDep) -> BacktestResponse:
    """"What if I'd followed him at N% risk?" — equity curve, drawdown,
    expectancy, through risk-based position sizing."""
    quotes = StockQuoteClient()
    try:
        service = TipBacktestService(repo=StockTipRepository(session), quotes=quotes)
        try:
            result = await service.backtest(
                tipster=body.tipster,
                starting_equity=body.starting_equity,
                risk_pct=body.risk_pct,
                stop_pct=body.stop_pct,
                apply_stop=body.apply_stop,
            )
        except (ValueError, DomainError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await quotes.aclose()
    return BacktestResponse(
        tipster=result.tipster,
        starting_equity=result.starting_equity,
        ending_equity=result.ending_equity,
        risk_pct=result.risk_pct,
        stop_pct=result.stop_pct,
        apply_stop=result.apply_stop,
        n_trades=result.n_trades,
        total_return_pct=result.total_return_pct,
        max_drawdown_pct=result.max_drawdown_pct,
        expectancy_r=result.expectancy_r,
        win_rate=result.win_rate,
        avg_days_held=result.avg_days_held,
        equity_curve=[
            EquityPointDTO(label=p.label, at=p.at, equity=p.equity) for p in result.equity_curve
        ],
        trades=[
            FollowTradeDTO(
                ticker=t.ticker,
                mentioned_at=t.mentioned_at,
                entry_price=t.entry_price,
                exit_fill=t.exit_fill,
                stop_price=t.stop_price,
                shares=t.shares,
                risk_amount=t.risk_amount,
                pnl=t.pnl,
                r_multiple=t.r_multiple,
                return_pct=t.return_pct,
                days_held=t.days_held,
                stopped_out=t.stopped_out,
                won=t.won,
            )
            for t in result.trades
        ],
        headline=result.headline,
    )


# ---------- analyst coverage (consensus target + per-firm ratings) ----------


class AnalystRatingDTO(BaseModel):
    firm: str
    rating: str
    action: str
    date: datetime


class AnalystConsensusDTO(BaseModel):
    target_mean: Decimal | None
    target_high: Decimal | None
    target_low: Decimal | None
    upside_pct: Decimal | None
    rating_key: str | None
    num_analysts: int | None
    strong_buy: int
    buy: int
    hold: int
    sell: int
    strong_sell: int


class AnalystSnapshotDTO(BaseModel):
    ticker: str
    available: bool
    current_price: Decimal | None
    consensus: AnalystConsensusDTO | None
    ratings: list[AnalystRatingDTO]
    note: str


_ANALYST_NOTE = (
    "Consensus target and per-bank ratings are from public data. Each bank's "
    "individual dollar price target and the Zacks Rank need a paid data source."
)


@router.get("/analyst/{ticker}", response_model=AnalystSnapshotDTO)
async def analyst(ticker: str) -> AnalystSnapshotDTO:
    """Wall-Street coverage for a ticker: consensus target + implied upside,
    consensus rating with its buy/hold/sell split, and each big bank's latest
    rating. Best-effort — returns available=false if the source is unreachable."""
    provider = YahooAnalystProvider()
    try:
        snap = await provider.fetch(ticker)
    finally:
        await provider.aclose()

    if snap is None:
        return AnalystSnapshotDTO(
            ticker=ticker.upper(),
            available=False,
            current_price=None,
            consensus=None,
            ratings=[],
            note=_ANALYST_NOTE,
        )

    consensus = None
    if snap.consensus is not None:
        c = snap.consensus
        consensus = AnalystConsensusDTO(
            target_mean=c.target_mean,
            target_high=c.target_high,
            target_low=c.target_low,
            upside_pct=c.upside_pct,
            rating_key=c.rating_key,
            num_analysts=c.num_analysts,
            strong_buy=c.strong_buy,
            buy=c.buy,
            hold=c.hold,
            sell=c.sell,
            strong_sell=c.strong_sell,
        )
    return AnalystSnapshotDTO(
        ticker=snap.ticker,
        available=True,
        current_price=snap.current_price,
        consensus=consensus,
        ratings=[
            AnalystRatingDTO(firm=r.firm, rating=r.rating, action=r.action, date=r.date)
            for r in snap.ratings
        ],
        note=_ANALYST_NOTE,
    )
