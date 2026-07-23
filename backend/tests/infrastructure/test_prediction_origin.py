"""Replayed predictions must never be counted as a track record."""

from __future__ import annotations

import inspect

from mentor.infrastructure.models import PredictionORM
from mentor.infrastructure.repositories.predictions import PredictionRepository


def test_predictions_record_where_they_came_from() -> None:
    assert hasattr(PredictionORM, "origin")


def test_the_honest_read_excludes_replays_by_default() -> None:
    """Regression: replayed rows were written into the same table as live
    ones with nothing to tell them apart, so a single button click silently
    mixed backfilled history into the paper P&L, the calibration chart and
    the post-mortem — with no way to separate them afterwards."""
    sig = inspect.signature(PredictionRepository.list_resolved)
    assert sig.parameters["include_replay"].default is False


def test_the_audit_log_shows_everything_that_was_written() -> None:
    """The one place replays should still appear — each row is labelled."""
    sig = inspect.signature(PredictionRepository.list_recent)
    assert sig.parameters["include_replay"].default is True


def test_the_replay_path_stamps_replay_without_being_asked() -> None:
    sig = inspect.signature(PredictionRepository.record_and_resolve)
    assert sig.parameters["origin"].default == "replay"


def test_the_live_path_stamps_live_without_being_asked() -> None:
    sig = inspect.signature(PredictionRepository.record)
    assert sig.parameters["origin"].default == "live"
