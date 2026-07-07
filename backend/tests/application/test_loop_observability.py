"""Tests for the loop's new senses: quality gate, paper P&L, health registry."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from mentor.application.forecasting.self_backtest import simulate_own_signals
from mentor.application.market.quality import DataQualityReport, GapWindow
from mentor.application.scheduler.health import LoopHealth
from mentor.application.scheduler.quality_gate import assess_quality, fx_market_open
from mentor.domain.market.bars import Timeframe

# A Tuesday 12:00 UTC — market unambiguously open.
_TUESDAY_NOON = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def _report(
    *,
    bars: int = 72,
    gaps: tuple[GapWindow, ...] = (),
    last_seen: datetime | None = None,
) -> DataQualityReport:
    return DataQualityReport(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        bars_scanned=bars,
        gaps=gaps,
        duplicate_count=0,
        last_seen_at=last_seen or _TUESDAY_NOON - timedelta(hours=1),
    )


# ---- fx_market_open ----


def test_market_closed_saturday_and_late_friday_open_sunday_night() -> None:
    saturday = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    friday_late = datetime(2026, 7, 10, 23, 0, tzinfo=UTC)
    sunday_early = datetime(2026, 7, 12, 12, 0, tzinfo=UTC)
    sunday_late = datetime(2026, 7, 12, 23, 0, tzinfo=UTC)
    assert fx_market_open(saturday) is False
    assert fx_market_open(friday_late) is False
    assert fx_market_open(sunday_early) is False
    assert fx_market_open(sunday_late) is True
    assert fx_market_open(_TUESDAY_NOON) is True


# ---- assess_quality ----


def test_healthy_window_passes() -> None:
    verdict = assess_quality(_report(), now=_TUESDAY_NOON)
    assert verdict.predict_ok is True


def test_empty_window_blocks() -> None:
    verdict = assess_quality(_report(bars=0), now=_TUESDAY_NOON)
    assert verdict.predict_ok is False


def test_weekend_gap_is_tolerated() -> None:
    # Friday 21:00 → Sunday 22:00 — the normal FX weekend hole (~49 bars).
    gap = GapWindow(
        expected_after=datetime(2026, 7, 10, 21, 0, tzinfo=UTC),
        next_seen=datetime(2026, 7, 12, 22, 0, tzinfo=UTC),
        missing_bars=48,
    )
    verdict = assess_quality(_report(gaps=(gap,)), now=_TUESDAY_NOON)
    assert verdict.predict_ok is True


def test_intraweek_gap_blocks() -> None:
    # Tuesday 02:00 → Tuesday 14:00 — a 11-bar hole with no weekend excuse.
    gap = GapWindow(
        expected_after=datetime(2026, 7, 7, 2, 0, tzinfo=UTC),
        next_seen=datetime(2026, 7, 7, 14, 0, tzinfo=UTC),
        missing_bars=11,
    )
    verdict = assess_quality(_report(gaps=(gap,)), now=_TUESDAY_NOON + timedelta(hours=3))
    assert verdict.predict_ok is False
    assert "feed hole" in verdict.reason


def test_stale_feed_during_open_market_blocks() -> None:
    verdict = assess_quality(
        _report(last_seen=_TUESDAY_NOON - timedelta(hours=10)),
        now=_TUESDAY_NOON,
    )
    assert verdict.predict_ok is False
    assert "stale" in verdict.reason


def test_stale_check_forgives_the_weekend_reopen() -> None:
    # Sunday 23:00: newest bar is Friday 21:00 (~50h old) — normal, not stale.
    sunday_reopen = datetime(2026, 7, 12, 23, 0, tzinfo=UTC)
    verdict = assess_quality(
        _report(last_seen=datetime(2026, 7, 10, 21, 0, tzinfo=UTC)),
        now=sunday_reopen,
    )
    assert verdict.predict_ok is True


# ---- paper trading over own signals ----


def _prediction(
    *,
    direction: str,
    entry: str,
    realised: str,
    confidence: str = "0.5",
    hours: int = 0,
) -> SimpleNamespace:
    asof = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=hours)
    return SimpleNamespace(
        asof=asof,
        horizon_at=asof + timedelta(hours=24),
        asof_close=Decimal(entry),
        realised_close=Decimal(realised),
        direction=direction,
        confidence=Decimal(confidence),
        p_up=Decimal("0.6"),
        realised_outcome=1,
    )


def test_paper_long_hit_and_short_hit_compound() -> None:
    rows = [
        _prediction(direction="long", entry="1.1000", realised="1.1110", hours=0),  # +1%
        _prediction(direction="short", entry="1.1110", realised="1.0999", hours=1),  # +1%
    ]
    report = simulate_own_signals(rows, spread=0.0)  # type: ignore[arg-type]
    assert report.trades == 2
    assert report.wins == 2
    assert report.total_return_pct > 1.9  # ~2.01% compounded


def test_paper_skips_neutral_and_low_confidence() -> None:
    rows = [
        _prediction(direction="neutral", entry="1.10", realised="1.20", hours=0),
        _prediction(direction="long", entry="1.10", realised="1.20", confidence="0.05", hours=1),
    ]
    report = simulate_own_signals(rows, min_confidence=0.2)  # type: ignore[arg-type]
    assert report.trades == 0
    assert report.skipped_neutral == 1
    assert report.skipped_low_confidence == 1


def test_paper_spread_turns_flat_trade_into_loss() -> None:
    rows = [_prediction(direction="long", entry="1.1000", realised="1.1000")]
    report = simulate_own_signals(rows, spread=0.0001)  # type: ignore[arg-type]
    assert report.trades == 1
    assert report.losses == 1
    assert report.total_return_pct < 0


# ---- health registry ----


def test_health_snapshot_orders_and_caps() -> None:
    health = LoopHealth(max_events=3)
    health.beat("predict", ok=True, note="fine")
    health.beat("ingest", ok=False, note="feed down")
    for i in range(5):
        health.event("quality_skip", f"skip {i}")
    beats, events = health.snapshot()
    assert [b["job"] for b in beats] == ["ingest", "predict"]  # sorted by job
    assert len(events) == 3  # ring buffer capped
    assert events[0]["detail"] == "skip 4"  # newest first
