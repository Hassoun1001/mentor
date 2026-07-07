"""Tip scoring — how did the tipster's calls actually do?

Pure functions only: given a tip's entry price and what the stock did
since, compute the honest return, and aggregate a scorecard by the
tipster's own categories and actions. No prediction here — this measures
outcomes that already happened, which is the only thing we can be honest
about.

Return is measured **since the tipster mentioned it** (entry = the close
on the mention date). Holding periods differ per tip, so the scorecard
reports the average holding window alongside the returns rather than
pretending they're comparable annualised figures.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from mentor.domain.tips.tip import TipAction


def _pct(now: Decimal, base: Decimal) -> Decimal:
    if base == 0:
        return Decimal("0")
    return ((now - base) / base * Decimal("100")).quantize(Decimal("0.01"))


@dataclass(frozen=True, slots=True)
class TipOutcome:
    ticker: str
    category: str
    action: str
    conviction: str
    note: str
    days_held: int
    mention_price: Decimal
    current_price: Decimal
    return_pct: Decimal
    max_drawup_pct: Decimal  # best unrealised gain since mention
    max_drawdown_pct: Decimal  # worst dip since mention
    dipped: bool | None  # for buy_on_dip: did it actually drop below entry?
    expected_move_pct: Decimal | None = None  # objective vol context (per ticker)
    vol_regime: str | None = None  # calm / normal / wide
    at_or_below_entry: bool = False  # a buy call trading at/below its mention price now
    daily_change_pct: Decimal | None = None  # last close vs the prior close


def build_outcome(
    *,
    ticker: str,
    category: str,
    action: str,
    conviction: str,
    note: str,
    days_held: int,
    mention_price: Decimal,
    current_price: Decimal,
    min_since: Decimal,
    max_since: Decimal,
) -> TipOutcome:
    dipped: bool | None = None
    if action == TipAction.BUY_ON_DIP.value:
        dipped = min_since < mention_price
    # A "dip alert": a buy/buy-on-dip call that's currently trading at or below
    # the price he named — i.e. it's back at his implied entry right now.
    buy_actions = (TipAction.BUY.value, TipAction.BUY_ON_DIP.value)
    at_or_below_entry = action in buy_actions and current_price <= mention_price
    return TipOutcome(
        ticker=ticker,
        category=category,
        action=action,
        conviction=conviction,
        note=note,
        days_held=days_held,
        mention_price=mention_price,
        current_price=current_price,
        return_pct=_pct(current_price, mention_price),
        max_drawup_pct=_pct(max_since, mention_price),
        max_drawdown_pct=_pct(min_since, mention_price),
        dipped=dipped,
        at_or_below_entry=at_or_below_entry,
    )


@dataclass(frozen=True, slots=True)
class ScorecardBucket:
    key: str
    count: int
    mean_return_pct: Decimal
    win_rate: Decimal  # fraction of tips with return > 0
    avg_days_held: Decimal
    best_ticker: str | None
    best_return_pct: Decimal
    worst_ticker: str | None
    worst_return_pct: Decimal


def _bucket(key: str, outcomes: Sequence[TipOutcome]) -> ScorecardBucket:
    n = len(outcomes)
    if n == 0:
        return ScorecardBucket(
            key=key,
            count=0,
            mean_return_pct=Decimal("0"),
            win_rate=Decimal("0"),
            avg_days_held=Decimal("0"),
            best_ticker=None,
            best_return_pct=Decimal("0"),
            worst_ticker=None,
            worst_return_pct=Decimal("0"),
        )
    total = sum((o.return_pct for o in outcomes), Decimal("0"))
    wins = sum(1 for o in outcomes if o.return_pct > 0)
    days = sum((Decimal(o.days_held) for o in outcomes), Decimal("0"))
    best = max(outcomes, key=lambda o: o.return_pct)
    worst = min(outcomes, key=lambda o: o.return_pct)
    return ScorecardBucket(
        key=key,
        count=n,
        mean_return_pct=(total / Decimal(n)).quantize(Decimal("0.01")),
        win_rate=(Decimal(wins) / Decimal(n)).quantize(Decimal("0.01")),
        avg_days_held=(days / Decimal(n)).quantize(Decimal("0.1")),
        best_ticker=best.ticker,
        best_return_pct=best.return_pct,
        worst_ticker=worst.ticker,
        worst_return_pct=worst.return_pct,
    )


@dataclass(frozen=True, slots=True)
class Scorecard:
    tipster: str
    total: int
    overall: ScorecardBucket
    by_category: tuple[ScorecardBucket, ...]
    by_action: tuple[ScorecardBucket, ...]
    dip_accuracy: Decimal | None  # of buy_on_dip calls, fraction that actually dipped
    headline: str


def build_scorecard(*, tipster: str, outcomes: Sequence[TipOutcome]) -> Scorecard:
    if not outcomes:
        return Scorecard(
            tipster=tipster,
            total=0,
            overall=_bucket("overall", []),
            by_category=(),
            by_action=(),
            dip_accuracy=None,
            headline="No priced tips yet — ingest a message to start the track record.",
        )

    by_cat: dict[str, list[TipOutcome]] = {}
    by_act: dict[str, list[TipOutcome]] = {}
    for o in outcomes:
        by_cat.setdefault(o.category, []).append(o)
        by_act.setdefault(o.action, []).append(o)

    dip_calls = [o for o in outcomes if o.dipped is not None]
    dip_accuracy: Decimal | None = None
    if dip_calls:
        dipped = sum(1 for o in dip_calls if o.dipped)
        dip_accuracy = (Decimal(dipped) / Decimal(len(dip_calls))).quantize(Decimal("0.01"))

    overall = _bucket("overall", outcomes)
    verdict = (
        "beating a coin flip" if overall.win_rate > Decimal("0.55") else "no better than chance"
    )
    headline = (
        f"{tipster}: {overall.count} tracked calls, average return "
        f"{overall.mean_return_pct}% over ~{overall.avg_days_held} days, "
        f"{int(overall.win_rate * 100)}% went up — {verdict}. "
        "Past calls don't predict future ones; this is a track record, not advice."
    )
    return Scorecard(
        tipster=tipster,
        total=len(outcomes),
        overall=overall,
        by_category=tuple(_bucket(k, v) for k, v in sorted(by_cat.items())),
        by_action=tuple(_bucket(k, v) for k, v in sorted(by_act.items())),
        dip_accuracy=dip_accuracy,
        headline=headline,
    )
