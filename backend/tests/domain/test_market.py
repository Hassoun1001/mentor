"""Market-data domain tests — bars and the quality scanner."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from mentor.application.market.quality import scan_quality
from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import PriceBar, Timeframe


def _bar(ts: datetime, *, high: Decimal | str = "1.09", low: Decimal | str = "1.08") -> PriceBar:
    return PriceBar(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        ts=ts,
        open=Decimal("1.085"),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal("1.088"),
        volume=Decimal("1000"),
        source="test",
    )


class TestPriceBar:
    def test_normalises_to_utc(self) -> None:
        bar = _bar(datetime(2026, 6, 25, 14, 30, tzinfo=UTC))
        assert bar.ts.tzinfo is UTC

    def test_naive_ts_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _bar(datetime(2026, 6, 25, 14, 30))

    def test_high_must_envelope(self) -> None:
        with pytest.raises(ValidationError):
            _bar(datetime(2026, 6, 25, tzinfo=UTC), high="1.0")

    def test_low_must_envelope(self) -> None:
        with pytest.raises(ValidationError):
            _bar(datetime(2026, 6, 25, tzinfo=UTC), low="2.0")


class TestQualityScanner:
    def _orm(self, ts: datetime) -> SimpleNamespace:
        # The scanner only reads `.ts` off the row.
        return SimpleNamespace(id=uuid.uuid4(), ts=ts)

    def test_no_gaps(self) -> None:
        start = datetime(2026, 6, 25, 9, tzinfo=UTC)
        bars = [self._orm(start + timedelta(hours=i)) for i in range(4)]
        report = scan_quality(symbol="EURUSD", timeframe=Timeframe.H1, bars=bars)
        assert report.gaps == ()
        assert report.bars_scanned == 4

    def test_detects_one_missing_bar(self) -> None:
        start = datetime(2026, 6, 25, 9, tzinfo=UTC)
        bars = [
            self._orm(start),
            self._orm(start + timedelta(hours=1)),
            # gap here — missing 11:00 bar
            self._orm(start + timedelta(hours=3)),
        ]
        report = scan_quality(symbol="EURUSD", timeframe=Timeframe.H1, bars=bars)
        assert len(report.gaps) == 1
        assert report.gaps[0].missing_bars == 1

    def test_empty(self) -> None:
        report = scan_quality(symbol="EURUSD", timeframe=Timeframe.H1, bars=[])
        assert report.bars_scanned == 0
        assert report.last_seen_at is None
