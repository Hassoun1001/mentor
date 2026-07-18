"""Batch-2 gate machinery: demotion hysteresis + lessons-driven pruning."""

from __future__ import annotations

import json
from pathlib import Path

from mentor.application.forecasting.promotion import PromotionService
from mentor.domain.forecasting.features import FEATURE_NAMES


def _service(tmp_path: Path) -> PromotionService:
    return PromotionService(model_store_dir=tmp_path)


# ---- demotion with hysteresis --------------------------------------------


def test_floor_streak_increments_and_demotes_at_three(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service._write_champion(name="champ", brier=0.29, family="technical")

    for expected, should_demote in [(1, False), (2, False), (3, True)]:
        champion = service.current_champion()
        assert champion is not None
        streak, demote = service._update_floor_streak(champion, 0.26)  # fails floor
        assert streak == expected
        assert demote is should_demote


def test_one_passing_regrade_resets_the_streak(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service._write_champion(name="champ", brier=0.29, family="technical", floor_failures=2)
    champion = service.current_champion()
    assert champion is not None
    streak, demote = service._update_floor_streak(champion, 0.20)  # passes floor
    assert streak == 0
    assert demote is False


def test_unmeasurable_regrade_neither_punishes_nor_forgives(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service._write_champion(name="champ", brier=0.29, family="technical", floor_failures=2)
    champion = service.current_champion()
    assert champion is not None
    streak, demote = service._update_floor_streak(champion, None)
    assert streak == 2
    assert demote is False


def test_demote_removes_the_pointer(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service._write_champion(name="champ", brier=0.29, family="technical")
    assert service.current_champion() is not None
    service._demote_champion()
    assert service.current_champion() is None


# ---- lessons-driven pruning ----------------------------------------------


def test_pruned_features_static_before_lessons(tmp_path: Path) -> None:
    service = _service(tmp_path)
    pruned = service._pruned_features()
    assert 6 <= len(pruned) < len(FEATURE_NAMES)
    assert set(pruned) <= set(FEATURE_NAMES)


def test_pruned_features_drop_dead_weight_from_lessons(tmp_path: Path) -> None:
    service = _service(tmp_path)
    # Two lessons where only four features carry importance.
    strong = {"ret_5": 0.5, "rsi_14": 0.3, "atr_pct": 0.15, "vol_20": 0.05}
    entry = {"at": "2026-01-01T00:00:00Z", "importances": strong}
    with (tmp_path / "lessons.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
        fh.write(json.dumps(entry) + "\n")
    pruned = service._pruned_features()
    # Dead features are gone; the minimum-count guard keeps at least 6, so
    # the four strong ones are certainly present and the set shrank.
    assert {"ret_5", "rsi_14", "atr_pct", "vol_20"} <= set(pruned)
    assert len(pruned) == 6  # min guard tops up from ranked leftovers


def test_pruned_features_preserve_canonical_order(tmp_path: Path) -> None:
    service = _service(tmp_path)
    pruned = service._pruned_features()
    indices = [FEATURE_NAMES.index(n) for n in pruned]
    assert indices == sorted(indices)
