"""FRED CSV parsing — skips missing '.' rows, parses dates + values."""

from __future__ import annotations

from datetime import UTC, datetime

from mentor.infrastructure.adapters.macro.fred import _parse_csv


def test_parse_skips_missing_and_bad_rows() -> None:
    csv = "observation_date,DGS2\n2026-01-02,4.10\n2026-01-03,.\n2026-01-06,4.20\nbadrow\n"
    obs = _parse_csv("DGS2", csv)
    assert [o.value for o in obs] == [4.10, 4.20]
    assert obs[0].series_id == "DGS2"
    assert obs[0].day == datetime(2026, 1, 2, tzinfo=UTC)
    assert all(o.day.tzinfo is not None for o in obs)


def test_parse_empty_returns_nothing() -> None:
    assert _parse_csv("DGS2", "observation_date,DGS2\n") == []
