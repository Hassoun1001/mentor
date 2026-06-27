"""The single most important test in the backtester:

a MarketView at index *i* exposes no API that can reach bar *i+1*.

We can't enumerate every possible attribute path, but we can enumerate
every *public* one and assert that none of them ever returns a bar with
a timestamp later than the view's `now`. If a future refactor adds an
attribute that leaks the future, this test will catch it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mentor.domain.backtest.market_view import MarketView
from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import PriceBar, Timeframe


def _series(n: int) -> tuple[PriceBar, ...]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return tuple(
        PriceBar(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            ts=start + timedelta(hours=i),
            open=Decimal("1.08") + Decimal(i) * Decimal("0.0001"),
            high=Decimal("1.0810") + Decimal(i) * Decimal("0.0001"),
            low=Decimal("1.0790") + Decimal(i) * Decimal("0.0001"),
            close=Decimal("1.0805") + Decimal(i) * Decimal("0.0001"),
            volume=Decimal("100"),
            source="test",
        )
        for i in range(n)
    )


class TestNoLookahead:
    def test_history_never_contains_future(self) -> None:
        bars = _series(40)
        for i in range(len(bars)):
            view = MarketView(_bars=bars, _current_index=i)
            for bar in view.history(100):
                assert bar.ts <= view.now, (
                    f"view at {i} returned bar with ts={bar.ts} > now={view.now}"
                )

    def test_closes_match_history(self) -> None:
        bars = _series(20)
        view = MarketView(_bars=bars, _current_index=10)
        assert view.closes(5) == tuple(b.close for b in bars[6:11])

    def test_previous_never_returns_future(self) -> None:
        bars = _series(20)
        view = MarketView(_bars=bars, _current_index=5)
        for n in range(1, 30):
            prev = view.previous(n)
            if prev is not None:
                assert prev.ts < view.now

    def test_previous_at_zero_returns_none(self) -> None:
        bars = _series(5)
        view = MarketView(_bars=bars, _current_index=0)
        assert view.previous(1) is None

    def test_rejects_out_of_range_index(self) -> None:
        bars = _series(3)
        with pytest.raises(ValidationError):
            MarketView(_bars=bars, _current_index=5)

    def test_public_api_does_not_include_obvious_future_accessors(self) -> None:
        """Any new public method/property that could leak the future
        will trip this test by name; rename or rethink before merging."""
        view = MarketView(_bars=_series(5), _current_index=2)
        forbidden = ("next", "future", "forward", "lookahead", "tomorrow", "ahead")
        for attr in dir(view):
            if attr.startswith("_"):
                continue
            assert not any(f in attr.lower() for f in forbidden), (
                f"public attribute {attr!r} looks like it might expose future data"
            )
