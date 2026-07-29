"""CFTC COT adapter — parsing, the net/OI transform, and publication dating.

No network: `parse_rows` is tested against hand-built rows shaped like the
CFTC Socrata response. The one thing that must never regress is the
publication-date lag, because dating COT at its report date instead of its
release date is the textbook lookahead bug.
"""

from __future__ import annotations

from datetime import UTC, datetime

from mentor.domain.forecasting.macro_features import COT_EUR_SERIES_ID
from mentor.infrastructure.adapters.macro.cftc_cot import _PUBLICATION_LAG, parse_rows


def _row(day: str, long_: object, short_: object, oi: object) -> dict[str, object]:
    return {
        "report_date_as_yyyy_mm_dd": day,
        "noncomm_positions_long_all": long_,
        "noncomm_positions_short_all": short_,
        "open_interest_all": oi,
    }


def test_net_over_open_interest_is_computed_and_signed() -> None:
    obs = parse_rows([_row("2026-07-21T00:00:00.000", 220465, 261803, 800061)], series_id="X")
    assert len(obs) == 1
    # (220465 - 261803) / 800061 = -0.05167 — net short.
    assert abs(obs[0].value - (-41338 / 800061)) < 1e-12
    assert obs[0].series_id == "X"


def test_the_observation_is_dated_at_publication_not_report() -> None:
    """Report is Tuesday; the value must not be visible until publication."""
    obs = parse_rows([_row("2026-07-21T00:00:00.000", 100, 50, 1000)], series_id="X")
    report = datetime(2026, 7, 21, tzinfo=UTC)
    assert obs[0].day == report + _PUBLICATION_LAG
    assert obs[0].day.strftime("%A") == "Saturday"  # Tue + 4 days


def test_rows_are_returned_in_publication_order() -> None:
    obs = parse_rows(
        [
            _row("2026-07-21T00:00:00.000", 100, 50, 1000),
            _row("2026-01-06T00:00:00.000", 100, 50, 1000),
            _row("2026-04-07T00:00:00.000", 100, 50, 1000),
        ],
        series_id="X",
    )
    assert [o.day for o in obs] == sorted(o.day for o in obs)


def test_bad_or_incomplete_rows_are_skipped_not_guessed() -> None:
    rows = [
        _row("2026-07-21T00:00:00.000", 100, 50, 1000),  # good
        _row("not-a-date", 100, 50, 1000),  # unparseable day
        _row("2026-07-14T00:00:00.000", None, 50, 1000),  # missing leg
        _row("2026-07-07T00:00:00.000", 100, 50, 0),  # zero open interest
        _row("2026-06-30T00:00:00.000", "x", 50, 1000),  # non-numeric
    ]
    obs = parse_rows(rows, series_id="X")
    assert len(obs) == 1


def test_duplicate_report_dates_keep_the_dominant_contract() -> None:
    """CFTC lists several "EURO FX" instruments; two rows can share a report
    date and would collide on (series_id, day) at upsert. The one with the
    most open interest wins — the contract whose positioning actually matters.
    Regression: the first live ingest hit exactly this CardinalityViolation."""
    rows = [
        _row("2026-07-21T00:00:00.000", 100, 50, 1000),  # small venue, OI 1000
        _row("2026-07-21T00:00:00.000", 200000, 260000, 800000),  # dominant, OI 800k
    ]
    obs = parse_rows(rows, series_id="X")
    assert len(obs) == 1
    assert abs(obs[0].value - ((200000 - 260000) / 800000)) < 1e-12


def test_default_series_id_matches_the_domain_constant() -> None:
    obs = parse_rows(
        [_row("2026-07-21T00:00:00.000", 100, 50, 1000)], series_id=COT_EUR_SERIES_ID
    )
    assert obs[0].series_id == "COT_EUR_NET_PCT_OI"
