"""Analyst domain helpers — firm matching, latest-per-firm, upside."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from mentor.domain.tips.analyst import (
    AnalystRating,
    compute_upside,
    latest_per_firm,
    match_firm,
)


def test_match_firm_canonicalises_the_watchlist() -> None:
    assert match_firm("JP Morgan") == "JPMorgan"
    assert match_firm("B of A Securities") == "Bank of America"
    assert match_firm("Morgan Stanley") == "Morgan Stanley"
    assert match_firm("Citigroup") == "Citi"
    assert match_firm("Goldman Sachs") == "Goldman Sachs"
    assert match_firm("Some Tiny Boutique") is None


def test_compute_upside() -> None:
    assert compute_upside(Decimal("150"), Decimal("100")) == Decimal("50.0")
    assert compute_upside(Decimal("80"), Decimal("100")) == Decimal("-20.0")
    assert compute_upside(None, Decimal("100")) is None
    assert compute_upside(Decimal("150"), Decimal("0")) is None


def test_latest_per_firm_keeps_newest_only() -> None:
    d1 = datetime(2026, 1, 1, tzinfo=UTC)
    d2 = datetime(2026, 6, 1, tzinfo=UTC)
    ratings = [
        AnalystRating(firm="UBS", rating="Neutral", action="main", date=d1),
        AnalystRating(firm="UBS", rating="Buy", action="up", date=d2),
        AnalystRating(firm="Citi", rating="Buy", action="main", date=d1),
    ]
    latest = latest_per_firm(ratings)
    assert len(latest) == 2
    ubs = next(r for r in latest if r.firm == "UBS")
    assert ubs.rating == "Buy"  # the newer one
    # newest first
    assert latest[0].date >= latest[1].date
